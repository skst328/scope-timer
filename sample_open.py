import time
from scope_timer.core import ScopeTimer


def func1():
    ScopeTimer.begin('level1')
    ScopeTimer.begin('level2')
    ScopeTimer.begin('level3')
    ScopeTimer.begin('level4')
    ScopeTimer.end('level4')



func1()

# 標準出力
ScopeTimer.summarize(verbose=False, precision=3)

# ファイル出力
ScopeTimer.save_txt('timer.log', precision=3)
ScopeTimer.save_html('timer.html', precision=3)
