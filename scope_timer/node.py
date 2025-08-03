import time
from typing import Optional

from rich.text import Text
from rich.tree import Tree

from scope_timer.record import TimerRecord
from scope_timer.stats import TimerStats
from scope_timer.infer import TimeProperty


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
        self.preprocessed = False

    def get_or_create_branch(self, name: str) -> "TimerNode":
        branch = self.branch_nodes.get(name)
        if branch is None:
            branch = TimerNode(name, level=self.level+1, parent=self)
            self.branch_nodes[name] = branch
        return branch

    def render_label(
        self,
        time_property: TimeProperty,
        max_label_length: int,
        max_time_length: int,
        max_ncall_length: int,
        verbose: bool = False):
        label = Text()

        node_label = f"[{self.name}]"

        # +3: for brackets and spacing
        label.append(f"{node_label:<{max_label_length+3}}", style="green")
        label.append(f"{time_property.format_time(self.total_time):>{max_time_length}} ")
        label.append(f"/ ")
        label.append(f"{self.ncall:>{max_ncall_length}}x ")

        if self.parent:
            if self.parent.total_time > 0:
                percent = round(self.total_time / self.parent.total_time * 100)
                label.append(f"({percent}%) ")
            else:
                label.append("(--%) ")
        if verbose:
            label.append(" [")
            label.append(f"min={time_property.format_time(self.min_time)}, ")
            label.append(f"max={time_property.format_time(self.max_time)}, ")
            label.append(f"avg={time_property.format_time(self.avg_time)}, ")
            label.append(f"var={time_property.format_time(self.var_time)}")
            label.append("]")
        return label

    def to_tree(
        self,
        time_property: TimeProperty,
        max_label_length: Optional[int] = None,
        max_time_length: Optional[int] = None,
        max_ncall_length: Optional[int] = None,
        verbose: bool = False
    ) -> Tree:
        if max_label_length is None:
            max_label_length = len(self.name)
        if max_time_length is None:
            max_time_length = len(time_property.format_time(self.total_time))
        if max_ncall_length is None:
            max_ncall_length = len(str(self.ncall))

        tree = Tree(
            self.render_label(
                time_property,
                max_label_length,
                max_time_length,
                max_ncall_length,
                verbose=verbose),
            guide_style="bright_blue"
        )

        if len(self.branch_nodes) > 0:
            max_label_length = max(len(node.name) for node in self.branch_nodes.values())
            max_time_length = max(len(time_property.format_time(node.total_time)) for node in self.branch_nodes.values())
            max_ncall_length = max(len(str(node.ncall)) for node in self.branch_nodes.values())
        else:
            max_label_length = None
            max_time_length = None
            max_ncall_length = None

        for branch_node in self.branch_nodes.values():
            tree.add(
                branch_node.to_tree(
                    time_property,
                    max_label_length,
                    max_time_length,
                    max_ncall_length,
                    verbose=verbose))
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
        if self.ncall == 0:
            return 0.
        return sum(r.elapsed for r in self.records[:self.ncall])

    def _get_min_time(self) -> float:
        if self.ncall == 0:
            return 0.
        return min(r.elapsed for r in self.records[:self.ncall])

    def _get_max_time(self) -> float:
        if self.ncall == 0:
            return 0.
        return max(r.elapsed for r in self.records[:self.ncall])

    def _get_avg_time(self) -> float:
        if self.ncall == 0:
            return 0.
        return self._get_total_time() / self.ncall

    def _get_var_time(self) -> float:
        if self.ncall < 2:
            return 0.
        avg = self._get_avg_time()
        return sum((r.elapsed - avg) ** 2 for r in self.records[:self.ncall]) / self.ncall

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
