import threading
import time
import random

# scope_timer.py として保存した、Canvasのコードをインポート
from scope_timer import ScopeTimer

# 全スレッドの結果を収集するための共有リストとロック
all_thread_results = []
lock = threading.Lock()

def task_b_worker():
    """プロセスBのワーカースレッド"""
    with ScopeTimer.profile("Task_B"):
        # ワーカースレッド内でも階層的な計測が可能
        with ScopeTimer.profile("SubTask_B1"):
            time.sleep(random.uniform(0.2, 0.4))
        with ScopeTimer.profile("SubTask_B2"):
            time.sleep(random.uniform(0.1, 0.3))

    # このスレッドの計測結果を共有リストに追加
    with lock:
        all_thread_results.append({
            "thread_name": threading.current_thread().name,
            "results": ScopeTimer.get_thread_results()
        })
    # このスレッドのタイマーをリセット
    ScopeTimer.reset()

def task_d_worker():
    """プロセスDのワーカースレッド"""
    with ScopeTimer.profile("Task_D"):
        time.sleep(random.uniform(0.1, 0.2))

    # このスレッドの計測結果を共有リストに追加
    with lock:
        all_thread_results.append({
            "thread_name": threading.current_thread().name,
            "results": ScopeTimer.get_thread_results()
        })
    # このスreadのタイマーをリセット
    ScopeTimer.reset()


def main():
    """メインの処理"""
    # --- トップレベルの計測を開始 ---
    with ScopeTimer.profile("Main_Process"):
        
        # --- A: メインスレッドでの処理 ---
        with ScopeTimer.profile("A"):
            print("--- プロセスB (2スレッド) を開始 ---")
            # --- B: 2スレッドでの並列処理 ---
            threads_b = []
            for i in range(2):
                thread = threading.Thread(target=task_b_worker, name=f"Thread-B-{i}")
                threads_b.append(thread)
                thread.start()
            
            for thread in threads_b:
                thread.join()
            print("--- プロセスB 終了 ---")

            print("\n--- プロセスC (メインスレッド) を開始 ---")
            # --- C: メインスレッドでの処理 ---
            with ScopeTimer.profile("C"):
                time.sleep(0.3)
            print("--- プロセスC 終了 ---")

            print("\n--- プロセスD (4スレッド) を開始 ---")
            # --- D: 4スレッドでの並列処理 ---
            threads_d = []
            for i in range(4):
                thread = threading.Thread(target=task_d_worker, name=f"Thread-D-{i}")
                threads_d.append(thread)
                thread.start()

            for thread in threads_d:
                thread.join()
            print("--- プロセスD 終了 ---")

    # --- レポートの表示 ---
    print("\n" + "="*50)
    
    # 1. メインスレッドのタイマーサマリーを表示
    print("メインスレッドの計測結果:")
    ScopeTimer.summarize()

    # 2. 全スレッドから収集した結果を集約して表示
    print("\n全スレッドの集計レポート:")
    ScopeTimer.aggregate_and_summarize(all_thread_results)
    
    print("="*50)


if __name__ == "__main__":
    main()
