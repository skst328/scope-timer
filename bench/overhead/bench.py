import os
import time
import argparse
import statistics
import importlib
from importlib.metadata import version
from pathlib import Path

# ───────────────────── parameter ─────────────────────
N_OUTER: int = 10      # outer loop count
N_MIDDLE: int = 10     # middle loop count
N_INNER: int = 100     # inner loop count
N_VEC: int = 32        # length of vectors

TEXT_FILE: Path = Path("comp_results.txt")

# ───────────────────── format function ─────────────────────
def format_row(row: list[str], widths: list[int]) -> str:
    return " | ".join(f"{v:<{w}}" for v, w in zip(row, widths))

# ────────────────────────── CLI entry ──────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="ScopeTimer overhead benchmark")
    parser.add_argument("-n", "--nruns", type=int, default=1, help="number of repetitions")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["on", "off", "native"],
        required=True,
    )
    args = parser.parse_args()

    if args.mode == 'native':
        workload = importlib.import_module("workload_native")
    else:
        os.environ["SCOPE_TIMER_ENABLE"] = '1' if args.mode == "on" else '0'
        workload = importlib.import_module("workload_instrumented")

    import scope_timer
    from scope_timer import ScopeTimer

    # Get version
    try:
        lib_version = scope_timer.__version__
    except AttributeError:
        lib_version = version("scope-timer")

    if args.mode == 'native':
        lib_version = '-'

    elapsed_list: list[float] = []

    for i in range(args.nruns):
        t0 = time.perf_counter()
        workload.run_once(
            N_OUTER,
            N_MIDDLE,
            N_INNER,
            N_VEC
        )
        t1 = time.perf_counter()

        elapsed = t1 - t0
        print(f"{i}: {elapsed=}")
        elapsed_list.append(elapsed)

        ScopeTimer.summarize(divider="rule")
        # ScopeTimer.reset()

    # nrecords
    n_records: int = N_OUTER * N_MIDDLE * N_INNER * N_VEC
    n_records_str: str = f"{n_records:,}"

    mean_elapsed = statistics.mean(elapsed_list)

    # Aggregate stats
    if len(elapsed_list) >= 2:
        stats = {
            "min": min(elapsed_list),
            "max": max(elapsed_list),
            "mean": mean_elapsed,
            "median": statistics.median(elapsed_list),
            "stdev": statistics.stdev(elapsed_list),
            "per_record": mean_elapsed / n_records,
        }
    else:
        stats = {
            "min": elapsed_list[0],
            "max": elapsed_list[0],
            "mean": elapsed_list[0],
            "median": elapsed_list[0],
            "stdev": 0.0,
            "per_record": mean_elapsed / n_records,
        }

    # Row to write
    row = [
        lib_version,
        args.mode,
        n_records_str,
        *(f"{stats[k] * 1000:.3f}" for k in ["min", "max", "mean", "median", "stdev"]),
        f"{stats['per_record'] * 1_000_000_000:.3f}",
    ]

    headers = ["version", "enabled", "nrecords", "min [ms]", "max [ms]", "mean [ms]", "median [ms]", "stdev [ms]", "per_record[ns]"]
    col_widths = [10, 7, 12, 10, 10, 10, 12, 13, 13]

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
