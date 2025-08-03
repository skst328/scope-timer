# tests/test_infer.py

import pytest
from scope_timer.infer import infer_time_property, _infer_time_unit, _infer_time_precision, _num_digits

@pytest.mark.parametrize("time_input, expected_unit", [
    (1.5, "s"),
    (0.5, "ms"),
    (0.0015, "ms"),
    (0.0005, "us"),
    (0.0, "us"),
])
def test_infer_time_unit(time_input, expected_unit):
    """Checks that the time unit is inferred correctly based on elapsed time."""
    assert _infer_time_unit(time_input, "auto") == expected_unit

@pytest.mark.parametrize("worst_time, unit, precision, expected_unit, expected_precision", [
    (2.5, "auto", "auto", "s", 5),      # Simple seconds
    (1500.0, "auto", "auto", "s", 2),  # Large seconds
    (0.5, "auto", "auto", "ms", 3),      # Sub-second
    (0.05, "auto", "auto", "ms", 4),     # Milliseconds
    (0.0005, "auto", "auto", "us", 1),   # Microseconds
    (10.0, "ms", 3, "ms", 3),           # Forced unit and precision
    (0.0, "auto", "auto", "us", 1),     # Zero time
    (1_234_567.0, "auto", "auto", "s", 0),  # digit >= precision_cap
    (0.0000005, "auto", "auto", "us", 1),  # digit <= 0
])
def test_infer_time_property(worst_time, unit, precision, expected_unit, expected_precision):
    """Checks the whole inference pipeline for units and precision."""
    prop = infer_time_property(worst_time, unit, precision)
    assert prop.unit == expected_unit
    assert prop.precision == expected_precision


@pytest.mark.parametrize("n, expected", [
    (0.999, 0),
])
def test_num_digits_for_sub_one_value(n, expected):
    """
    Directly tests the _num_digits branch for numbers < 1.
    This covers line 50, accepting it's currently dormant.
    """
    assert _num_digits(n) == expected
