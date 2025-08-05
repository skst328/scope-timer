import argparse
import math
import random
import statistics
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
import scope_timer
from scope_timer import ScopeTimer

# ───────────────────────── Parameters ──────────────────────────
N_OUTER = 10             # outer loop count
N_MIDDLE = 10            # middle loop count
N_INNER = 100            # inner loop count  → 100 000 scopes total
VEC_DIM = 32             # length of vectors used in np.dot
TEXT_FILE = Path("comp_results.txt")

# ───────────────────── Workload definition ─────────────────────

@ScopeTimer.profile("inner.sin")
def inner_sin(x):
    math.sin(x)

@ScopeTimer.profile("inner.dot")
def inner_dot():
    a = np.random.rand(VEC_DIM)
    b = np.random.rand(VEC_DIM)
    _ = np.dot(a, b)

@ScopeTimer.profile("compute_many")
def compute_many() -> None:
    """Generate a huge number of short profiling scopes."""
    for _ in range(N_OUTER):
        with ScopeTimer.profile("outer"):
            base = random.random()
            for _ in range(N_MIDDLE):
                with ScopeTimer.profile("middle"):
                    for k in range(N_INNER):
                        inner_sin(base + k)
                        inner_dot()

@ScopeTimer.profile("pipeline")
def run_once() -> None:
    """One complete benchmark iteration."""
    compute_many()

# Utility: format table row
def format_row(row: list[str], widths: list[int]) -> str:
    return " | ".join(f"{v:<{w}}" for v, w in zip(row, widths))


# ────────────────────────── CLI entry ──────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="ScopeTimer overhead benchmark")
    parser.add_argument("-n", "--runs", type=int, default=1, help="number of repetitions")
    parser.add_argument("--disable", action="store_true", help="disable ScopeTimer profiling")
    args = parser.parse_args()

    # Set timer state
    if args.disable:
        ScopeTimer.disable()

    # Get version
    try:
        lib_version = scope_timer.__version__
    except AttributeError:
        lib_version = version("scope-timer")

    elapsed_list: list[float] = []

    for i in range(args.runs):
        t0 = time.perf_counter()
        run_once()
        t1 = time.perf_counter()

        elapsed = t1 - t0
        print(f"{i}: {elapsed=}")
        elapsed_list.append(elapsed)

        ScopeTimer.summarize(divider="rule")
        # ScopeTimer.reset()

    # Aggregate stats
    if len(elapsed_list) >= 2:
        stats = {
            "min": min(elapsed_list),
            "max": max(elapsed_list),
            "mean": statistics.mean(elapsed_list),
            "median": statistics.median(elapsed_list),
            "stdev": statistics.stdev(elapsed_list),
        }
    else:
        stats = {
            "min": elapsed_list[0],
            "max": elapsed_list[0],
            "mean": elapsed_list[0],
            "median": elapsed_list[0],
            "stdev": 0.0,
        }

    # Row to write
    row = [
        lib_version,
        "ON" if not args.disable else "OFF",
        str(args.runs),
        *(f"{stats[k]:.3f}" for k in ["min", "max", "mean", "median", "stdev"])
    ]

    headers = ["version", "enabled", "runs", "min [ms]", "max [ms]", "mean [ms]", "median [ms]", "stdev [ms]"]
    col_widths = [10, 7, 5, 10, 10, 10, 12, 10]

    # Print to console (optional)
    print("\nBenchmark result:")
    print(format_row(headers, col_widths))
    print("-" * (sum(col_widths) + 3 * (len(headers) - 1)))
    print(format_row(row, col_widths))

    # Append to file
    write_header = not TEXT_FILE.exists() or TEXT_FILE.stat().st_size == 0
    with TEXT_FILE.open("a", encoding="utf-8") as f:
        if write_header:
            f.write(format_row(headers, col_widths) + "\n")
            f.write("-" * (sum(col_widths) + 3 * (len(headers) - 1)) + "\n")
        f.write(format_row(row, col_widths) + "\n")


if __name__ == "__main__":
    main()
