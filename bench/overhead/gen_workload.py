import jinja2

# テンプレートファイルを読み込む
env = jinja2.Environment(loader=jinja2.FileSystemLoader('.'))
template = env.get_template('workload.py.j2')

# 1. タイマー「あり」のバージョンを生成 (workload_instrumented.py)
#    ScopeTimerの記述がすべて含まれる
output_on = template.render(timer_enabled=True)
with open('workload_instrumented.py', 'w', encoding='utf-8') as f:
    f.write(output_on)
print("Generated workload_instrumented.py (with timer calls)")

# 2. タイマー「なし」のバージョンを生成 (workload_native.py)
#    ScopeTimerの記述が完全に除去される
output_off = template.render(timer_enabled=False)
with open('workload_native.py', 'w', encoding='utf-8') as f:
    f.write(output_off)
print("Generated workload_native.py (pure native code)")
