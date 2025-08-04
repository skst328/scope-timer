from scope_timer import ScopeTimer
import time

@ScopeTimer.profile("preprocess")
def preprocess():
    with ScopeTimer.profile("load_data"):
        time.sleep(0.01)
    with ScopeTimer.profile("clean_data"):
        time.sleep(0.015)

@ScopeTimer.profile("compute")
def compute():
    for _ in range(10):
        with ScopeTimer.profile("matmul"):
            time.sleep(0.001)
        with ScopeTimer.profile("activation"):
            time.sleep(0.0005)

@ScopeTimer.profile("postprocess")
def postprocess():
    with ScopeTimer.profile("save_results"):
        time.sleep(0.005)

# Profile the entire pipeline
with ScopeTimer.profile("pipeline"):
    preprocess()
    compute()
    postprocess()

# Print the summary to the console
ScopeTimer.summarize()

# You can also save the report to a file
ScopeTimer.save_html("timer_report.html")
