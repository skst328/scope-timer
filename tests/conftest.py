import pytest
from scope_timer import ScopeTimer

@pytest.fixture(autouse=True)
def reset_timer():
    """
    Reset the timer and re-enable it before each test to ensure isolation.
    This fixture is automatically applied to all tests.
    """
    ScopeTimer.reset()
    yield
