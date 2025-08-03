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
    with ScopeTimer.profile("log_metrics"):
        time.sleep(0.002)

@ScopeTimer.profile("pipeline")
def run_pipeline():
    preprocess()
    compute()
    postprocess()

@ScopeTimer.profile("main")
def main():
    for _ in range(2):
        run_pipeline()

if __name__ == "__main__":
    main()
    ScopeTimer.summarize()
