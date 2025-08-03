from typing import Optional
from dataclasses import dataclass


@dataclass(slots=True)
class TimerRecord:
    begin: float = 0.
    end: Optional[float] = None

    @property
    def elapsed(self) -> float:
        if self.end is None:
            return 0.
        return self.end - self.begin


