import math
from dataclasses import dataclass
from typing import Literal, Union


@dataclass(slots=True, frozen=True)
class TimeProperty:
    unit: Literal["s", "ms", "us"]
    scale: int
    precision: int

    def format_time(self, second_time: float) -> str:
        scaled = second_time * self.scale
        return f"{scaled:.{self.precision}f}{self.unit}"


def _infer_time_unit(
    second_time: float,
    time_unit: Literal["auto", "s", "ms", "us"]
) -> Literal["s", "ms", "us"]:
    if time_unit in ("s", "ms", "us"):
        return time_unit

    ONE_SECOND = 1.0
    ONE_MILISECOND = 0.001

    if second_time >= ONE_SECOND:
        return "s"
    elif second_time >= ONE_MILISECOND:
        return "ms"
    else:
        return "us"


def _infer_time_scaling(
    time_unit: Literal["s", "ms", "us"]
) -> int:
    match time_unit:
        case "s":
            return 1
        case "ms":
            return 1_000
        case "us":
            return 1_000_000


def _num_digits(n: float) -> int:
    n_int = int(n)
    if n_int == 0:
        return 0  # pragma: no cover
    return int(math.log10(abs(n_int))) + 1


def _infer_time_precision(
    second_time: float,
    time_unit: Literal["s", "ms", "us"],
    scale: int,
    precision: Union[int, Literal["auto"]]
) -> int:
    if isinstance(precision, int):
        return precision

    scaled_time = second_time * scale

    if time_unit == "us":
        return 1

    precision_cap = 6
    digit = _num_digits(scaled_time)

    if digit >= precision_cap:
        return 0
    if digit <= 0:
        return precision_cap  # pragma: no cover

    return precision_cap - digit


def infer_time_property(
    worst_time: float,
    unit: Literal["auto", "s", "ms", "us"],
    precision: Union[int, Literal["auto"]]
) -> TimeProperty:
    time_unit = _infer_time_unit(worst_time, unit)
    time_scale = _infer_time_scaling(time_unit)
    time_precision = _infer_time_precision(
        worst_time, time_unit, time_scale, precision)

    return TimeProperty(
        unit=time_unit,
        scale=time_scale,
        precision=time_precision
    )
