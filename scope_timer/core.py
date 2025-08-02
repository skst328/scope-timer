import io
import time
import threading
from typing import Optional, Union, Literal
from dataclasses import dataclass
from contextlib import contextmanager
from pathlib import Path

from rich.text import Text
from rich.tree import Tree
from rich.panel import Panel
from rich.rule import Rule
from rich.console import Console, Group


@dataclass(slots=True)
class TimerRecord:
    begin: float = 0.
    end: Optional[float] = None

    @property
    def elapsed(self) -> float:
        if self.end is None:
            return 0.
        return self.end - self.begin


@dataclass(slots=True, frozen=True)
class TimerStats:
    total: float
    min_: float
    max_: float
    avg: float
    var_: float


class TimerNode:
    name: str
    records: list[TimerRecord]
    level: int
    branch_nodes: dict[str, "TimerNode"]
    parent: Optional["TimerNode"]
    ncall: int
    is_root: bool
    stats: Optional[TimerStats]
    preprocessed: bool

    __slots__ = [
        "name",
        "records",
        "level",
        "branch_nodes",
        "parent",
        "ncall",
        "is_root",
        "stats",
        "preprocessed"
    ]

    def __init__(
        self,
        name: str,
        level: int = 0,
        parent: Optional["TimerNode"] = None,
    ):
        self.name = name
        self.records = []
        self.level = level
        self.branch_nodes = {}
        self.parent = parent
        self.ncall = 0
        self.is_root = True if level == 0 else False
        self.stats = None
        self.preprocessed = False

    def begin_record(self):
        self.records.append(
            TimerRecord(begin=time.perf_counter())
        )

    def end_record(self):
        self.records[self.ncall].end = time.perf_counter()
        self.ncall += 1

    def get_or_create_branch(self, name: str) -> "TimerNode":
        branch = self.branch_nodes.get(name)
        if branch is None:
            branch = TimerNode(name, level=self.level+1, parent=self)
            self.branch_nodes[name] = branch
        return branch

    def render_label(self, precision: int, verbose: bool = False):
        label = Text()
        label.append(f"[{self.name}]", style="bright_green")
        label.append(f" {self.total_time:.{precision}f}sec / {self.ncall}x")

        if verbose:
            label.append(" (")
            label.append(f"min={self.min_time:.{precision}f}, ")
            label.append(f"max={self.max_time:.{precision}f}, ")
            label.append(f"avg={self.avg_time:.{precision}f}, ")
            label.append(f"var={self.var_time:.{precision}f}")
            label.append(")")
        return label

    def to_tree(self, precision: int, verbose: bool = False) -> Tree:
        tree = Tree(
            self.render_label(precision, verbose=verbose),
            guide_style="bright_blue"
        )
        for branch_node in self.branch_nodes.values():
            tree.add(branch_node.to_tree(precision, verbose=verbose))
        return tree

    def has_open_record(self) -> bool:
        return self.ncall < len(self.records)

    def get_open_nodes(self) -> list["TimerNode"]:
        open_nodes: list["TimerNode"] = []

        if self.has_open_record():
            open_nodes.append(self)

        for branch_node in self.branch_nodes.values():
            open_nodes.extend(branch_node.get_open_nodes())
        return open_nodes

    def _get_total_time(self) -> float:
        return sum(r.elapsed for r in self.records)

    def _get_min_time(self) -> float:
        return min(r.elapsed for r in self.records)

    def _get_max_time(self) -> float:
        return max(r.elapsed for r in self.records)

    def _get_avg_time(self) -> float:
        if self.ncall == 0:
            return 0.
        return self._get_total_time() / self.ncall

    def _get_var_time(self) -> float:
        if self.ncall == 0:
            return 0.
        avg = self._get_avg_time()
        return sum((r.elapsed - avg) ** 2 for r in self.records) / self.ncall

    @property
    def total_time(self) -> float:
        if self.stats is None:
            return self._get_total_time()
        return self.stats.total

    @property
    def min_time(self) -> float:
        if self.stats is None:
            return self._get_min_time()
        return self.stats.min_

    @property
    def max_time(self) -> float:
        if self.stats is None:
            return self._get_max_time()
        return self.stats.max_

    @property
    def avg_time(self) -> float:
        if self.stats is None:
            return self._get_avg_time()
        return self.stats.avg

    @property
    def var_time(self) -> float:
        if self.stats is None:
            return self._get_var_time()
        return self.stats.var_

    def _build_stats(self):
        self.stats = TimerStats(
            total=self._get_total_time(),
            min_=self._get_min_time(),
            max_=self._get_max_time(),
            avg=self._get_avg_time(),
            var_=self._get_var_time()
        )

    def build_stats_recursive(self):
        self._build_stats()
        for branch_node in self.branch_nodes.values():
            branch_node.build_stats_recursive()
        self.preprocessed = True


class TimerThreadLocal(threading.local):
    active_node: Optional[TimerNode]
    root_nodes: dict[str, TimerNode]

    def __init__(self):
        self.active_node = None
        self.root_nodes = {}

    def reset(self):
        self.active_node = None
        self.root_nodes.clear()


class ScopeTimer:
    _local: TimerThreadLocal = TimerThreadLocal()

    @staticmethod
    def begin(name: str):
        tlocal = ScopeTimer._local

        active_node = tlocal.active_node
        if active_node is None:
            node = tlocal.root_nodes.get(name)
            if node is None:
                node = TimerNode(name, level=0, parent=None)
                tlocal.root_nodes[name] = node
        else:
            node = active_node.get_or_create_branch(name)

        tlocal.active_node = node
        node.begin_record()

    @staticmethod
    def end(name: str):
        tlocal = ScopeTimer._local

        active_node = tlocal.active_node

        if active_node is None:
            raise ValueError(
                f"end() was called for '{name}' without a matching begin()."
            )
        if active_node.name != name:
            raise ValueError(
                f"Timer mismatch: expected end('{active_node.name}'), but got end('{name}'). "
                "Make sure your begin()/end() calls are correctly paired and nested."
            )

        active_node.end_record()

        tlocal.active_node = None if active_node.is_root else active_node.parent

    @staticmethod
    @contextmanager
    def profile(name: str):
        ScopeTimer.begin(name)
        try:
            yield
        finally:
            ScopeTimer.end(name)

    @staticmethod
    def reset():
        ScopeTimer._local.reset()

    @staticmethod
    def _create_rich_group(
            verbose: bool = False,
            precision: int = 4,
            divider: Literal["rule", "blank"] = "blank"
    ):
        tlocal = ScopeTimer._local
        overall_time: float = 0.

        items = []

        title = Panel(f"ScopeTimer Summary", style="white", expand=False)
        items.append(title)

        tree_list = []
        warn_list: list[Text] = []
        for root_node in tlocal.root_nodes.values():
            tree = root_node.to_tree(precision, verbose=verbose)
            tree_list.append(tree)
            if divider == "rule":
                tree_list.append(Rule(style="grey50"))
            elif divider == "blank":
                tree_list.append(Text())
            overall_time += root_node.total_time

            for open_node in root_node.get_open_nodes():
                warn_msg = Text(
                    f"- unclosed scope: '{open_node.name}'",
                    style="yellow")
                warn_list.append(warn_msg)

        if len(warn_list) > 0:
            warn_msg = Text(
                f"WARNING: {len(warn_list)} unfinished scope(s) detected. "
                "They are excluded from totals.",
                style="yellow"
            )
            items.append(warn_msg)
            items.extend(warn_list)
            if divider == "rule":
                items.append(Rule(style="grey50"))
            elif divider == "blank":
                items.append(Text())

        items.extend(tree_list)

        footer = Text(f"overall_time: {overall_time:.{precision}f} sec", style="bright_red")
        items.append(footer)

        group = Group(*items)
        return group

    @staticmethod
    def _preprocess():
        tlocal = ScopeTimer._local
        for root_node in tlocal.root_nodes.values():
            if root_node.preprocessed is False:
                root_node.build_stats_recursive()

    @staticmethod
    def summarize(
        precision: Union[int, Literal["auto"]] = "auto",
        time_unit: Literal["auto", "s", "ms", "us"] = "auto",
        divider: Literal["rule", "blank"] = "rule",
        verbose: bool = False
    ):
        ScopeTimer._preprocess()
        group = ScopeTimer._create_rich_group(
            verbose=verbose, precision=precision, divider=divider)
        console = Console()
        console.print(group)

    @staticmethod
    def save_txt(
        file_path: Union[str, Path],
        precision: int = 4,
        verbose: bool = False
    ):
        ScopeTimer._preprocess()
        path = Path(file_path)
        group = ScopeTimer._create_rich_group(
            verbose=verbose, precision=precision, divider="blank")

        with path.open("w", encoding="utf-8") as f:
            console = Console(file=f, color_system=None, force_terminal=False)
            console.print(group)

    @staticmethod
    def save_html(
        file_path: Union[str, Path],
        precision: int=4,
        verbose: bool = False
    ):
        ScopeTimer._preprocess()
        path = Path(file_path)
        group = ScopeTimer._create_rich_group(
            verbose=verbose, precision=precision, divider="blank")

        sink = io.StringIO()
        console = Console(record=True, file=sink)
        console.print(group)
        html = console.export_html()
        path.write_text(html, encoding="utf-8")
