import pytest
from scope_timer.record import TimerRecord

def test_record_elapsed_with_end_time():
    """Checks that the elapsed time is calculated correctly when an end time exists."""
    record = TimerRecord(begin=100.0, end=100.5)
    assert pytest.approx(record.elapsed) == 0.5

def test_record_elapsed_with_no_end_time():
    """
    Checks that the elapsed time is 0.0 when the end time is not set.
    """
    record = TimerRecord(begin=123.45, end=None)
    assert record.elapsed == 0.0
