import time
import threading
from contextlib import contextmanager
from collections import defaultdict

# richライブラリをインポート
from rich import print
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree


class TimerRecord(object):
    """個々のタイマー区間のデータを保持するクラス"""
    def __init__(self, name, top, level, parent=None):
        self.name = name
        self.time_records = {}
        self.ncall = 0
        self.top = top
        self.child_nodes = {}
        self.level = level
        self.parent = parent

    def begin_record(self):
        self.time_records[self.ncall] = {
            'begin': time.perf_counter(),
            'end': 0,
            'elapsed': 0,
        }

    def end_record(self):
        if self.ncall not in self.time_records:
            return
        self.time_records[self.ncall]['end'] = time.perf_counter()
        self.time_records[self.ncall]['elapsed'] = \
            self.time_records[self.ncall]['end'] - self.time_records[self.ncall]['begin']
        self.ncall += 1

    def create_and_add_child(self, name):
        child = TimerRecord(name, top=False, level=self.level + 1, parent=self)
        self.child_nodes[name] = child
        return child

    def get_total_time(self):
        return sum(r['elapsed'] for r in self.time_records.values())

    def get_msg(self, hl=True, verbose=True, precision=4):
        """ファイル書き出し用のプレーンテキストを生成するメソッド"""
        msg = []
        prefix = '    ' * self.level
        msg.append(prefix + f"[Timer name: {self.name}]")
        
        total_time_per_record = self.get_total_time()
        
        if verbose:
            for i, t in self.time_records.items():
                msg.append(prefix + f"call No {i}: {t['elapsed']:.{precision}f} [sec]")
        
        msg.append(prefix + f"total   : {total_time_per_record:.{precision}f} [sec]")
        if len(self.time_records) > 1:
            msg.append(prefix + f"per call: {total_time_per_record / len(self.time_records):.{precision}f} [sec]")
        msg.append(prefix + f"ncall   : {len(self.time_records)}")
        return msg, total_time_per_record

class ScopeTimer(object):
    """スレッドセーフな階層的タイマー"""
    _local = threading.local()

    @staticmethod
    def _initialize_thread_state():
        """現在のスレッドのタイマー状態を初期化する"""
        if not hasattr(ScopeTimer._local, 'initialized'):
            ScopeTimer._local.cur_node = None
            ScopeTimer._local.top_nodes = dict()
            ScopeTimer._local.initialized = True

    @staticmethod
    @contextmanager
    def profile(name):
        ScopeTimer.begin(name)
        try:
            yield
        finally:
            ScopeTimer.end(name)

    @staticmethod
    def begin(name, show_msg=False):
        ScopeTimer._initialize_thread_state()
        if show_msg:
            print(Panel(f" Begin {name} ", style="green", subtitle="start"))

        cur_node = ScopeTimer._local.cur_node
        if cur_node is None:
            tr = ScopeTimer._local.top_nodes.get(name)
            if tr is None:
                tr = TimerRecord(name, top=True, level=0)
                ScopeTimer._local.top_nodes[name] = tr
        else:
            tr = cur_node.child_nodes.get(name)
            if tr is None:
                tr = cur_node.create_and_add_child(name)
        
        ScopeTimer._local.cur_node = tr
        tr.begin_record()

    @staticmethod
    def end(name, show_msg=False):
        ScopeTimer._initialize_thread_state()
        cur_node = ScopeTimer._local.cur_node
        
        if cur_node is None:
            raise ValueError(f"end() was called for '{name}' without a matching begin().")
        if cur_node.name != name:
            raise ValueError(f"Timer mismatch: expecting end() for '{cur_node.name}', but got '{name}'.")
        
        cur_node.end_record()

        if cur_node.top:
            ScopeTimer._local.cur_node = None
        else:
            ScopeTimer._local.cur_node = cur_node.parent

        if show_msg:
            print(Panel(f" End {name} ", style="green", subtitle="end"))

    @staticmethod
    def reset():
        """現在のスレッドのタイマー記録をすべてリセットする"""
        ScopeTimer._local.cur_node = None
        ScopeTimer._local.top_nodes = dict()

    @staticmethod
    def get_thread_results():
        """現在のスレッドの計測結果(top_nodes)を返す"""
        ScopeTimer._initialize_thread_state()
        return ScopeTimer._local.top_nodes

    @staticmethod
    def summarize(verbose=True, precision=4, hl=True):
        """現在のスレッドのサマリーをrich.Treeを使って表示する"""
        ScopeTimer._initialize_thread_state()
        
        def _add_node_to_tree(record: TimerRecord, tree_branch: Tree):
            total_time = record.get_total_time()
            ncall = len(record.time_records)
            lines = []
            title_style = "cyan" if hl else "default"
            lines.append(f"[{title_style}][Timer name: {record.name}][/{title_style}]")
            lines.append(f"total   : {total_time:.{precision}f} [sec]")
            if ncall > 1:
                lines.append(f"per call: {total_time / ncall:.{precision}f} [sec]")
            lines.append(f"ncall   : {ncall}")
            if verbose:
                lines.append("\n[dim]Individual calls:[/dim]")
                for i, t in record.time_records.items():
                    lines.append(f"[dim]call No {i}: {t['elapsed']:.{precision}f} [sec][/dim]")
            label_str = "\n".join(lines)
            new_branch = tree_branch.add(label_str)
            for child in record.child_nodes.values():
                _add_node_to_tree(child, new_branch)

        tree = Tree("", guide_style="bold bright_blue")
        total_time = 0
        for tn in ScopeTimer._local.top_nodes.values():
            _add_node_to_tree(tn, tree)
            total_time += tn.get_total_time()

        total_str_style = "bold magenta" if hl else "default"
        total_str = f"[{total_str_style}]total: {total_time:.{precision}f} [sec][/{total_str_style}]"

        summary_panel = Panel(tree, title="[bold green]Timer Summary (Current Thread)[/bold green]",
                              title_align="left", subtitle=total_str, subtitle_align="right",
                              border_style="green", expand=False)
        print(summary_panel)

    @staticmethod
    def aggregate_and_summarize(all_results, precision=4, hl=True):
        """
        ★★★ ここからが修正されたコード ★★★
        全スレッドの結果を集約し、階層構造を維持したレポートを表示する。
        """
        
        # 集約されたノードのデータを保持するためのヘルパークラス
        class MergedRecord:
            def __init__(self, name):
                self.name = name
                self.children = {}  # { 'child_name': MergedRecord, ... }
                self.threads = {}   # { 'thread_name': TimerRecord, ... }

        # 再帰的にツリー構造をマージする関数
        def merge_into(target_node: MergedRecord, source_node: TimerRecord, thread_name: str):
            target_node.threads[thread_name] = source_node
            for child_name, child_node in source_node.child_nodes.items():
                if child_name not in target_node.children:
                    target_node.children[child_name] = MergedRecord(child_name)
                merge_into(target_node.children[child_name], child_node, thread_name)

        # 1. 全スレッドの階層構造を一つの`merged_top_nodes`にマージする
        merged_top_nodes = {}
        for res in all_results:
            thread_name = res['thread_name']
            for node_name, node_obj in res['results'].items():
                if node_name not in merged_top_nodes:
                    merged_top_nodes[node_name] = MergedRecord(node_name)
                merge_into(merged_top_nodes[node_name], node_obj, thread_name)

        # 再帰的にマージされたツリーをrich.Treeにレンダリングする関数
        def render_merged_tree(merged_node: MergedRecord, tree_branch: Tree):
            # リージョン全体の統計を計算
            overall_total_time = sum(r.get_total_time() for r in merged_node.threads.values())
            
            # リージョンのラベルを作成
            region_label = Text()
            region_label.append(f"[Timer name: {merged_node.name}]\n", style="cyan")
            region_label.append(f"Overall Total: {overall_total_time:.{precision}f} [sec]")
            region_branch = tree_branch.add(region_label)

            # スレッドごとの詳細をサブブランチとして追加
            for thread_name, record in sorted(merged_node.threads.items()):
                total_time = record.get_total_time()
                ncall = record.ncall
                
                thread_label = Text()
                thread_label.append(f"[{thread_name}]", style="yellow")
                thread_label.append(f"\n  total   : {total_time:.{precision}f} [sec]")
                if ncall > 1:
                    thread_label.append(f"\n  per call: {total_time/ncall:.{precision}f} [sec]")
                thread_label.append(f"\n  ncall   : {ncall}")
                region_branch.add(thread_label)

            # 子ノードに対して再帰的にレンダリング
            for child_name, child_merged_node in sorted(merged_node.children.items()):
                render_merged_tree(child_merged_node, region_branch)

        # --- レポート生成のメインロジック ---
        tree = Tree("", guide_style="bold bright_blue")
        grand_total_time = 0

        # 2. マージされたトップノードからレンダリングを開始
        for node_name, merged_node in sorted(merged_top_nodes.items()):
            render_merged_tree(merged_node, tree)
            # トップレベルのノード時間のみを合計に加算
            grand_total_time += sum(r.get_total_time() for r in merged_node.threads.values())

        total_str_style = "bold magenta" if hl else "default"
        total_str = f"[{total_str_style}]Grand Total: {grand_total_time:.{precision}f} [sec][/{total_str_style}]"
        
        summary_panel = Panel(tree, title="[bold green]Aggregated Timer Report[/bold green]",
                              title_align="left", subtitle=total_str, subtitle_align="right",
                              border_style="green", expand=False)
        print(summary_panel)

    @staticmethod
    def write(fname, verbose=True, precision=4):
        """現在のスレッドのサマリーをプレーンテキストでファイルに書き出す"""
        ScopeTimer._initialize_thread_state()
        output_lines = ["--- Timer Summary (Current Thread) ---"]
        total_time = 0
        for tn in ScopeTimer._local.top_nodes.values():
            nodes_to_process = [tn]
            while nodes_to_process:
                node = nodes_to_process.pop(0)
                _msg_lines, total_time_per_record = node.get_msg(hl=False, verbose=verbose, precision=precision)
                output_lines.extend(_msg_lines)
                if node.top:
                    total_time += total_time_per_record
                nodes_to_process.extend(node.child_nodes.values())
        
        output_lines.append("-" * 21)
        output_lines.append(f"total: {total_time:.{precision}f} [sec]")
        with open(fname, mode='w', encoding='utf-8') as f:
            f.write("\n".join(output_lines))

