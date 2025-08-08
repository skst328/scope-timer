import pytest
import time
from pathlib import Path

from scope_timer import ScopeTimer

# Tolerance for time.sleep() inaccuracy, set to 10%
TOLERANCE = 0.1


def test_simple_profile():
    """Checks that basic profiling works within a tolerance."""
    sleep_interval = 0.01
    with ScopeTimer.profile_block("simple"):
        time.sleep(sleep_interval)

    # Access internal data for validation
    node = ScopeTimer._local.root_nodes["simple"]
    assert node.ncall == 1
    # Check if the measured time is within the acceptable range
    assert sleep_interval <= node.total_time <= sleep_interval * (1 + TOLERANCE)

def test_nesting():
    """Checks that nested scopes are measured correctly."""
    parent_sleep = 0.01
    child_sleep = 0.02
    total_sleep = parent_sleep * 2 + child_sleep

    with ScopeTimer.profile_block("parent"):
        time.sleep(parent_sleep)
        with ScopeTimer.profile_block("child"):
            time.sleep(child_sleep)
        time.sleep(parent_sleep)

    parent_node = ScopeTimer._local.root_nodes["parent"]
    child_node = parent_node.branch_nodes["child"]

    assert parent_node.ncall == 1
    assert child_node.ncall == 1
    assert parent_node.total_time >= child_node.total_time
    assert total_sleep <= parent_node.total_time <= total_sleep * (1 + TOLERANCE)

def test_loop_and_stats():
    """Checks behavior in a loop and validates statistics."""
    n_loops = 5
    sleep_interval = 0.01
    for _ in range(n_loops):
        with ScopeTimer.profile_block("loop"):
            time.sleep(sleep_interval)

    ScopeTimer._preprocess("auto", "auto")  # Force stats calculation
    node = ScopeTimer._local.root_nodes["loop"]

    assert node.ncall == n_loops
    # Check stats against the tolerance
    assert sleep_interval <= node.avg_time <= sleep_interval * (1 + TOLERANCE)
    assert node.min_time > 0
    assert node.max_time > 0

def test_reset():
    """Checks that the reset functionality works as expected."""
    with ScopeTimer.profile_block("test_reset"):
        pass

    assert "test_reset" in ScopeTimer._local.root_nodes
    ScopeTimer.reset()
    assert not ScopeTimer._local.root_nodes

def test_fixed_unfinished_scope_bug():
    """Ensures the previously fixed 'unfinished scope' bug does not regress."""
    sleep_interval = 0.01
    # Run 3 completed calls
    for _ in range(3):
        with ScopeTimer.profile_block("bug_check"):
            time.sleep(sleep_interval)

    # Create one unclosed call
    ScopeTimer._begin("bug_check")

    ScopeTimer._preprocess("auto", "auto")
    node = ScopeTimer._local.root_nodes["bug_check"]

    assert node.ncall == 3
    # Check that min_time is not zero (proof of the bug fix)
    assert sleep_interval <= node.min_time <= sleep_interval * (1 + TOLERANCE)

def test_mismatched_end_raises_error():
    """Checks that a ValueError is raised for mismatched begin/end calls."""
    with pytest.raises(ValueError) as excinfo:
        ScopeTimer._begin("A")
        ScopeTimer._end("B")

    # Check that the error message contains the expected string
    assert "Timer mismatch" in str(excinfo.value)

def test_end_without_begin_raises_error():
    """Checks that a ValueError is raised if end() is called with no active scope."""
    with pytest.raises(ValueError):
        ScopeTimer._end("lonely_end")

def test_save_txt(tmp_path: Path):
    """Checks that save_txt() creates a non-empty file."""
    file_path = tmp_path / "timer.log"
    with ScopeTimer.profile_block("save_test"):
        time.sleep(0.01)

    ScopeTimer.save_txt(file_path, verbose=True)

    assert file_path.exists()
    assert file_path.read_text()
    assert "save_test" in file_path.read_text()
    assert "avg=" in file_path.read_text() # Check verbose output

def test_save_html(tmp_path: Path):
    """Checks that save_html() creates a non-empty HTML file."""
    file_path = tmp_path / "timer.html"
    with ScopeTimer.profile_block("save_test_html"):
        time.sleep(0.01)

    ScopeTimer.save_html(file_path, verbose=True)

    assert file_path.exists()
    content = file_path.read_text()
    assert "<html>" in content
    assert "save_test_html" in content
    assert "avg=" in content # Check verbose output

def test_summarize_unfinished_warning(capsys):
    """Checks that summarize() prints a warning for unfinished scopes."""
    ScopeTimer._begin("unfinished")
    ScopeTimer.summarize()
    captured = capsys.readouterr()
    assert "WARNING" in captured.out
    assert "unclosed scope: 'unfinished'" in captured.out

def test_create_rich_group_raises_without_preprocess():
    """
    Checks that calling _create_rich_group before _preprocess raises a RuntimeError.
    This covers line 119.
    """
    with ScopeTimer.profile_block("test"):
        pass # Create some data

    # Directly call the internal method without preprocessing
    with pytest.raises(RuntimeError):
        ScopeTimer._create_rich_group()

def test_summarize_unfinished_warning_with_blank_divider(capsys):
    """
    Checks the divider="blank" option when an unfinished scope warning is present.
    This covers lines 153-154.
    """
    ScopeTimer._begin("unfinished_blank")
    # Call summarize with the specific divider option
    ScopeTimer.summarize(divider="blank")
    captured = capsys.readouterr()

    # Just checking that it runs without error and produces a warning is enough
    assert "WARNING" in captured.out
    assert "unclosed scope: 'unfinished_blank'" in captured.out

def test_profiling_disabled_by_env_var(monkeypatch):
    """
    Checks that profiling is fully disabled when SCOPE_TIMER_ENABLE=0.
    This requires reloading the module to respect the environment variable.
    """
    # _TIMER_ENABLEフラグを直接0に書き換える
    monkeypatch.setattr(ScopeTimer, "_TIMER_ENABLE", 0)

    with ScopeTimer.profile_block("should_not_be_recorded"):
        time.sleep(0.01)

    # Verify no scopes were created
    assert not ScopeTimer._local.root_nodes

def test_profile_func_decorator_with_inferred_name():
    """
    Checks that the @profile_func decorator works, using the function's
    own name as the scope name. This covers the enabled path.
    """
    @ScopeTimer.profile_func()
    def my_decorated_function():
        """A simple decorated function."""
        time.sleep(0.01)

    my_decorated_function()

    assert "my_decorated_function" in ScopeTimer._local.root_nodes
    node = ScopeTimer._local.root_nodes["my_decorated_function"]
    assert node.ncall == 1
    assert node.total_time >= 0.01

def test_profile_func_decorator_with_custom_name():
    """
    Checks that the @profile_func decorator works with a custom name
    provided as an argument.
    """
    @ScopeTimer.profile_func("custom_decorator_scope")
    def another_decorated_function():
        time.sleep(0.01)

    another_decorated_function()

    assert "custom_decorator_scope" in ScopeTimer._local.root_nodes
    assert "another_decorated_function" not in ScopeTimer._local.root_nodes

def test_profile_func_preserves_function_metadata():
    """
    Checks that @profile_func preserves the original function's metadata
    (like __name__ and __doc__) thanks to @wraps.
    """
    @ScopeTimer.profile_func()
    def function_with_docstring():
        """This is a test docstring."""
        pass

    assert function_with_docstring.__name__ == "function_with_docstring"
    assert function_with_docstring.__doc__ == "This is a test docstring."

def test_profile_func_is_noop_when_disabled(monkeypatch):
    """
    Checks that the @profile_func decorator does nothing and returns the
    original function when the timer is disabled. This covers the disabled path.
    """
    # Temporarily disable the timer by patching the internal flag
    monkeypatch.setattr(ScopeTimer, "_TIMER_ENABLE", 0)

    @ScopeTimer.profile_func()
    def undecorated_equivalent_function():
        return "expected_value"

    # Call the function and check its return value
    result = undecorated_equivalent_function()
    assert result == "expected_value"

    # Verify that no profiling data was recorded
    assert not ScopeTimer._local.root_nodes
