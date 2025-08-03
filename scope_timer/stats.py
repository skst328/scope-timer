from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TimerStats:
    total: float
    min_: float
    max_: float
    avg: float
    var_: float
