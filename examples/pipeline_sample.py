from scope_timer import ScopeTimer
import time


@ScopeTimer.profile_func("preprocess")
def preprocess():
    with ScopeTimer.profile_block("load_data"):
        time.sleep(0.01)
    with ScopeTimer.profile_block("clean_data"):
        time.sleep(0.015)

@ScopeTimer.profile_func("compute")
def compute():
    for _ in range(10):
        with ScopeTimer.profile_block("matmul"):
            time.sleep(0.001)
        with ScopeTimer.profile_block("activation"):
            time.sleep(0.0005)

@ScopeTimer.profile_func("postprocess")
def postprocess():
    with ScopeTimer.profile_block("save_results"):
        time.sleep(0.005)
    with ScopeTimer.profile_block("log_metrics"):
        time.sleep(0.002)

@ScopeTimer.profile_func("pipeline")
def run_pipeline():
    preprocess()
    compute()
    postprocess()

@ScopeTimer.profile_func("main")
def main():
    for _ in range(2):
        run_pipeline()

if __name__ == "__main__":
    main()
    ScopeTimer.summarize()

    ScopeTimer.reset()
    main()
    ScopeTimer.summarize()

    main()
    ScopeTimer.summarize()
