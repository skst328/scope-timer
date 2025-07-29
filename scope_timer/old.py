import time

import shutil

from contextlib import contextmanager

from rich import print
from rich.panel import Panel
from rich.text import Text


class Colors:
    BLACK        = '\033[30m'  # NOQA
    RED          = '\033[31m'  # NOQA
    GREEN        = '\033[32m'  # NOQA
    YELLOW       = '\033[33m'  # NOQA
    BLUE         = '\033[34m'  # NOQA
    MAGENTA      = '\033[35m'  # NOQA
    CYAN         = '\033[36m'  # NOQA
    WHITE        = '\033[37m'  # NOQA
    COLOR_DEFAULT= '\033[39m'  # NOQA
    BOLD         = '\033[1m'   # NOQA
    UNDERLINE    = '\033[4m'   # NOQA
    INVISIBLE    = '\033[08m'  # NOQA
    REVERCE      = '\033[07m'  # NOQA
    BG_BLACK     = '\033[40m'  # NOQA
    BG_RED       = '\033[41m'  # NOQA
    BG_GREEN     = '\033[42m'  # NOQA
    BG_YELLOW    = '\033[43m'  # NOQA
    BG_BLUE      = '\033[44m'  # NOQA
    BG_MAGENTA   = '\033[45m'  # NOQA
    BG_CYAN      = '\033[46m'  # NOQA
    BG_WHITE     = '\033[47m'  # NOQA
    BG_DEFAULT   = '\033[49m'  # NOQA
    RESET        = '\033[0m'   # NOQA


def to_hl(msg, color, hl=True):
    if hl:
        return color + msg + Colors.RESET
    else:
        return msg


class TimerRecord(object):

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
        # end()が呼ばれる前にbegin()が呼ばれていることを保証
        if self.ncall not in self.time_records:
            return # or raise an error

        self.time_records[self.ncall]['end'] = time.perf_counter()
        self.time_records[self.ncall]['elapsed'] = \
            self.time_records[self.ncall]['end'] - \
            self.time_records[self.ncall]['begin']
        self.ncall += 1

    def create_and_add_child(self, name):
        child = TimerRecord(
            name, top=False, level=self.level + 1, parent=self)
        self.child_nodes[name] = child
        return child

    def get_msg(self, level, hl=True, verbose=True, precision=4):
        msg = []
        level = self.level
        # ★修正点: インデントを半角スペース4つに戻しました
        init_prefix = '    ' * level
        prefix = '    ' * level
        msg.append(init_prefix + to_hl(f'[Timer name: {self.name}]', Colors.CYAN, hl))
        
        total_time_per_record = 0
        for i, t in self.time_records.items():
            if verbose:
                msg.append(
                    prefix + f"call No {i}: {t['elapsed']:.{precision}f} [sec]"
                )
            total_time_per_record += t['elapsed']
        
        msg.append(
            prefix + f"total   : {total_time_per_record:.{precision}f} [sec]"
        )
        
        # ★修正点: ゼロ除算を防止
        if len(self.time_records) > 0:
            msg.append(
                prefix + f"per call: {total_time_per_record / len(self.time_records):.{precision}f} [sec]"
            )

        msg.append(prefix + f"ncall   : {len(self.time_records)}")

        return msg, total_time_per_record

    def get_nodes_recursive(self):
        # ★★★ 最も重要な修正点 ★★★
        # forループがelseブロックの外に出ていたのを修正しました
        if len(self.child_nodes) == 0:
            return [self]
        else:
            ret = [self]
            for c in self.child_nodes.values():
                for cn in c.get_nodes_recursive():
                    ret.append(cn)
            return ret

    def __str__(self):
        # __str__内で存在しない変数を参照していたため修正
        total_time = sum(r['elapsed'] for r in self.time_records.values())
        msg = [
            f'name: {self.name}',
            f'total_time: {total_time}',
            f'ncall: {self.ncall}',
        ]
        return '\n'.join(msg)


def _create_msg_for_terminal_size(msg_base):
    try:
        terminal_size = shutil.get_terminal_size().columns
    except OSError:
        # 非対話的環境ではターミナルサイズが取得できないことがある
        terminal_size = 80
        
    half_size = (terminal_size - len(msg_base)) // 2
    msg = '-' * half_size + msg_base + '-' * half_size
    if len(msg) < terminal_size:
        msg += '-'
    return msg


class ScopeTimer(object):
    cur_node = None
    top_nodes = dict()

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
        if show_msg:
            msg = _create_msg_for_terminal_size(f' Begin {name} ')
            print(to_hl(msg, Colors.GREEN, True))

        cur_node = ScopeTimer.cur_node
        if cur_node is None:
            tr = ScopeTimer.top_nodes.get(name)
            if tr is None:
                tr = TimerRecord(name, top=True, level=0)
                ScopeTimer.top_nodes[name] = tr
        else:
            tr = cur_node.child_nodes.get(name)
            if tr is None:
                tr = cur_node.create_and_add_child(name)
        
        ScopeTimer.cur_node = tr
        tr.begin_record()

    @staticmethod
    def end(name, show_msg=False):
        if show_msg:
            msg = _create_msg_for_terminal_size(f' End {name} ') + '\n'
            print(to_hl(msg, Colors.GREEN, True))

        cur_node = ScopeTimer.cur_node
        
        # ★修正点: begin()なしでend()が呼ばれた場合のエラーを防止
        if cur_node is None:
            raise ValueError(f"end() was called for '{name}' without a matching begin().")
        
        if cur_node.name != name:
            raise ValueError(f"Timer mismatch: expecting end() for '{cur_node.name}', but got '{name}'.")
        
        cur_node.end_record()

        if cur_node.top:
            ScopeTimer.cur_node = None
        else:
            ScopeTimer.cur_node = cur_node.parent

    @staticmethod
    def summarize(verbose=True, precision=4, hl=True):
        msg = []
        msg.append(to_hl(
            _create_msg_for_terminal_size(' Timer Summary '),
            Colors.GREEN,
            hl)
        )
        total_time = 0
        for tn in ScopeTimer.top_nodes.values():
            all_nodes = tn.get_nodes_recursive()
            for node in all_nodes:
                _msg, total_time_per_record = node.get_msg(
                    node.level, hl, verbose=verbose, precision=precision)
                msg += _msg
                if node.top:
                    total_time += total_time_per_record
        
        msg.append(
            to_hl(
                f'total: {total_time:.{precision}f} [sec]',
                Colors.BG_RED, hl))
        msg.append(to_hl(
            _create_msg_for_terminal_size(''),
            Colors.GREEN,
            hl
        ))
        msg.append('')
        return '\n'.join(msg)

    @staticmethod
    def write(fname, verbose=True, precision=4):
        with open(fname, mode='w') as f:
            f.write(
                ScopeTimer.summarize(
                    hl=False, verbose=verbose, precision=precision
                )
            )
