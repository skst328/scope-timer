import pytest
import threading
import time
from typing import List, Dict
from scope_timer import ScopeTimer
from scope_timer.node import TimerNode

# Tolerance for time.sleep() inaccuracy (15%)
TOLERANCE = 0.15

@pytest.fixture(autouse=True)
def reset_timer():
    """Reset the timer before each test to ensure isolation."""
    ScopeTimer.reset()
    yield

def worker(
    thread_id: int,
    n_loops: int,
    sleep_interval: float,
    results_list: List[Dict[str, TimerNode]],
    lock: threading.Lock
):
    """
    Target function executed by each thread.
    It measures time using thread-specific scope names and appends its results
    to a shared list for the main thread to verify.
    """
    # A unique root scope for each thread
    root_scope_name = f"thread_{thread_id}_root"

    for i in range(n_loops):
        with ScopeTimer.profile(root_scope_name):
            # First level child scope
            with ScopeTimer.profile("child_A"):
                time.sleep(sleep_interval)

            # Second level child scope
            with ScopeTimer.profile("child_B"):
                time.sleep(sleep_interval / 2)
                with ScopeTimer.profile("grandchild_B1"):
                    time.sleep(sleep_interval / 4)

    # Use a lock to safely append the thread-local results to the shared list
    with lock:
        results_list.append(ScopeTimer._local.root_nodes.copy())

    # Clean up the thread-local data
    ScopeTimer.reset()

def test_multithread_isolation():
    """
    Verifies that when multiple threads use the timer simultaneously,
    the measurement results for each thread remain separate and independent.
    """
    n_threads = 4
    n_loops = 5
    sleep_interval = 0.01

    threads = []
    results = []
    lock = threading.Lock()

    for i in range(n_threads):
        thread = threading.Thread(
            target=worker,
            args=(i, n_loops, sleep_interval, results, lock)
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # --- Verification ---

    # Check that we have collected results from all threads
    assert len(results) == n_threads

    # Verify the results from each thread individually
    # The order of results is not guaranteed, so we check based on content
    all_found_roots = set()
    for thread_nodes in results:
        # Each thread should have generated exactly one root node
        assert len(thread_nodes) == 1

        root_node = list(thread_nodes.values())[0]
        root_scope_name = root_node.name
        all_found_roots.add(root_scope_name)

        # Check that the number of calls matches the number of loops
        assert root_node.ncall == n_loops

        # Check that child scopes are also recorded correctly
        assert "child_A" in root_node.branch_nodes
        assert "child_B" in root_node.branch_nodes

        child_a_node = root_node.branch_nodes["child_A"]
        child_b_node = root_node.branch_nodes["child_B"]

        assert child_a_node.ncall == n_loops
        assert child_b_node.ncall == n_loops

        # Check that grandchild scopes are also recorded correctly
        assert "grandchild_B1" in child_b_node.branch_nodes
        grandchild_b1_node = child_b_node.branch_nodes["grandchild_B1"]
        assert grandchild_b1_node.ncall == n_loops

        # Check that the average execution time of each scope is within the expected range
        expected_total_sleep = sleep_interval + sleep_interval / 2 + sleep_interval / 4
        root_node.build_stats_recursive() # Calculate stats for verification

        assert sleep_interval <= child_a_node.avg_time <= sleep_interval * (1 + TOLERANCE)
        assert grandchild_b1_node.avg_time > 0
        assert expected_total_sleep <= root_node.avg_time <= expected_total_sleep * (1 + TOLERANCE)

    # Finally, ensure that all expected root scopes were found across the results
    expected_roots = {f"thread_{i}_root" for i in range(n_threads)}
    assert all_found_roots == expected_roots
