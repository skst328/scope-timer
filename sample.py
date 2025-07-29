import numpy as np
from scope_timer import ScopeTimer


# 測定対象の関数その1
def func1(x, n_iter):
    ScopeTimer.begin('func1')
    for i in range(n_iter):
        x += 1
    ScopeTimer.end('func1')


# 測定対象の関数その2
@ScopeTimer.profile('func2')
def func2(x, n_iter):
    # 関数その2のサブ関数
    def func2_sub(x):
        ScopeTimer.begin('func2_sub')
        retval = 2 * x
        ScopeTimer.end('func2_sub')
        return retval

    for i in range(n_iter):
        x += x / func2_sub(x)


x = np.arange(100000, dtype='f4')
with ScopeTimer.profile('Scope1'):
    func1(x, 10000)
    func2(x, 10000)


with ScopeTimer.profile('Scope2'):
    y = np.ones(1000, dtype='f4')
    func2(y, 10000)


# 標準出力
ScopeTimer.summarize(verbose=False, precision=6)

# ファイル出力
ScopeTimer.write('timer.log', verbose=True, precision=6)
