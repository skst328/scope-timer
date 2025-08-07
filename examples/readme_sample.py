from scope_timer import ScopeTimer
import time

@ScopeTimer.profile_func()
def preprocess():
    with ScopeTimer.profile_block("load_data"):
        time.sleep(0.01)
    with ScopeTimer.profile_block("clean_data"):
        time.sleep(0.015)

@ScopeTimer.profile_func()
def compute():
    for _ in range(10):
        with ScopeTimer.profile_block("matmul"):
            time.sleep(0.001)
        with ScopeTimer.profile_block("activation"):
            time.sleep(0.0005)

@ScopeTimer.profile_func()
def postprocess():
    with ScopeTimer.profile_block("save_results"):
        time.sleep(0.005)

# Profile the entire pipeline
with ScopeTimer.profile_block("pipeline"):
    preprocess()
    compute()
    postprocess()

# Print the summary to the console
ScopeTimer.summarize()

# You can also save the report to a file
ScopeTimer.save_html("timer_report.html")
