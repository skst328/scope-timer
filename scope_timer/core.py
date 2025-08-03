import io
from typing import Union, Literal
from contextlib import contextmanager
from pathlib import Path

from rich.text import Text
from rich.panel import Panel
from rich.rule import Rule
from rich.console import Console, Group

from scope_timer.node import TimerNode
from scope_timer.thread_local import TimerThreadLocal
from scope_timer.infer import infer_time_property



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
            divider: Literal["rule", "blank"] = "blank"
    ):
        tlocal = ScopeTimer._local
        overall_time: float = 0.

        time_property = tlocal.time_property
        if time_property is None:
            raise RuntimeError

        items = []

        title = Panel(f"ScopeTimer Summary", style="white", expand=False)
        items.append(title)

        tree_list = []
        warn_list: list[Text] = []
        for root_node in tlocal.root_nodes.values():
            tree = root_node.to_tree(time_property, verbose=verbose)
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

        if len(warn_list) < len(tlocal.root_nodes):
            footer = Text(f"overall_time: {time_property.format_time(overall_time)}", style="bright_red")
        else:
            footer = Text("overall_time: N/A (no completed root scopes)", style="bright_red")
        items.append(footer)

        group = Group(*items)
        return group

    @staticmethod
    def _preprocess(
        time_unit: Literal["auto", "s", "ms", "us"],
        precision: Union[int, Literal["auto"]]
    ):
        tlocal = ScopeTimer._local

        worst_time: float = 0.
        for root_node in tlocal.root_nodes.values():
            if not root_node.preprocessed:
                root_node.build_stats_recursive()

            if root_node.total_time > worst_time:
                worst_time = root_node.total_time

        tlocal.time_property = infer_time_property(
            worst_time,
            time_unit,
            precision
        )

    @staticmethod
    def summarize(
        time_unit: Literal["auto", "s", "ms", "us"] = "auto",
        precision: Union[int, Literal["auto"]] = "auto",
        divider: Literal["rule", "blank"] = "rule",
        verbose: bool = False
    ):
        ScopeTimer._preprocess(time_unit, precision)
        group = ScopeTimer._create_rich_group(
            verbose=verbose, divider=divider)
        console = Console()
        console.print(group)

    @staticmethod
    def save_txt(
        file_path: Union[str, Path],
        time_unit: Literal["auto", "s", "ms", "us"] = "auto",
        precision: Union[int, Literal["auto"]] = "auto",
        verbose: bool = False
    ):
        ScopeTimer._preprocess(time_unit, precision)
        path = Path(file_path)
        group = ScopeTimer._create_rich_group(
            verbose=verbose, divider="blank")

        with path.open("w", encoding="utf-8") as f:
            console = Console(file=f, color_system=None, force_terminal=False)
            console.print(group)

    @staticmethod
    def save_html(
        file_path: Union[str, Path],
        time_unit: Literal["auto", "s", "ms", "us"] = "auto",
        precision: Union[int, Literal["auto"]] = "auto",
        verbose: bool = False
    ):
        ScopeTimer._preprocess(time_unit, precision)
        path = Path(file_path)
        group = ScopeTimer._create_rich_group(
            verbose=verbose, divider="blank")

        sink = io.StringIO()
        console = Console(record=True, file=sink)
        console.print(group)
        html = console.export_html()
        path.write_text(html, encoding="utf-8")
