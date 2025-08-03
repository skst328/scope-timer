[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![CI](https://github.com/skst328/scope-timer/actions/workflows/ci.yml/badge.svg)


# scope-timer

A lightweight profiler to measure execution time with a rich and colorful hierarchical report.

`scope-timer` makes it easy to find performance bottlenecks in your Python code by timing specific sections and presenting the results in a beautiful, hierarchical tree. It's designed to be simple to use and have minimal overhead.

## Key Features

* **Simple and Intuitive API**: Use decorators (`@ScopeTimer.profile(...)`) or context managers (`with ScopeTimer.profile(...)`) to profile code blocks effortlessly.
* **Hierarchical Reports**: Understand performance bottlenecks in nested function calls and scopes.
* **Multiple Outputs**: View reports directly in the console, or save them as plain text or interactive HTML files.
* **Rich & Colorful**: Powered by the `rich` library for beautiful and readable terminal output.
* **Lightweight & Predictable**: Low memory overhead and linear performance scaling, suitable for complex applications.
* **Thread-Safe**: Profile multi-threaded applications without interference between threads.

## Installation

```bash
pip install scope-timer
```

## Usage

You can easily profile functions and code blocks. Here is a simple example of a multi-stage pipeline:

```python
from scope_timer import ScopeTimer
import time

@ScopeTimer.profile("preprocess")
def preprocess():
    with ScopeTimer.profile("load_data"):
        time.sleep(0.01)
    with ScopeTimer.profile("clean_data"):
        time.sleep(0.015)

@ScopeTimer.profile("compute")
def compute():
    for _ in range(10):
        with ScopeTimer.profile("matmul"):
            time.sleep(0.001)
        with ScopeTimer.profile("activation"):
            time.sleep(0.0005)

@ScopeTimer.profile("postprocess")
def postprocess():
    with ScopeTimer.profile("save_results"):
        time.sleep(0.005)

# Profile the entire pipeline
with ScopeTimer.profile("pipeline"):
    preprocess()
    compute()
    postprocess()

# Print the summary to the console
ScopeTimer.summarize(verbose=True)

# You can also save the report to a file
ScopeTimer.save_html("timer_report.html")
```

## Example Output

The following console output shows a structured report with elapsed time, number of calls, and percentage of parent scope.

<p align="center">
  <img src="https://raw.githubusercontent.com/skst328/scope-timer/main/images/screenshot.png" alt="ScopeTimer Console Output" width="400">
</p>

## Limitations

Currently, `scope-timer` does **not support** `asyncio`.

This is because timer state is tracked **per thread**, but `asyncio` runs multiple tasks **within a single thread**, frequently switching execution contexts using `await`. As a result:

- Profiling an `async def` function with `@ScopeTimer.profile` may produce **incorrect timing** or even raise `ValueError`.
- Using `ScopeTimer.profile(...)` across an `await` boundary is **not safe**.

> For now, `scope-timer` is intended for synchronous or multi-threaded code only.

Support for async contexts (e.g., `contextvars`) may be considered in a future release.

## Performance

`scope-timer` is designed to be lightweight with predictable performance.
The following graphs show the memory usage and report generation time when profiling a realistic, multi-stage pipeline.

<p align="center"> <img src="https://raw.githubusercontent.com/skst328/scope-timer/main/images/scope_timer_performance.png" alt="ScopeTimer Performance Graph" width="90%"> </p>

This benchmark simulates a typical pipeline structure consisting of the following:

* `preprocess`: stage with 2 sub-tasks
* `compute`: stage with 1 sub-task and 20 repeated prediction scopes
* `postprocess`: stage with a result-saving scope

The full pipeline is executed multiple times (10–1000 iterations), and ScopeTimer.summarize() is called once at the end.

As shown:

* Memory usage increases linearly and remains well under 3MB for 1000 pipeline runs.
* Execution time for summarize() stays under 10ms for large workloads.

This ensures stable and low overhead behavior even in performance-critical applications.



## API Overview

All methods are static and can be called directly from the `ScopeTimer` class.

### Core Profiling Methods


* `ScopeTimer.profile(name: str)`

  The recommended way to profile a block of code. It can be used as a context manager (`with`) or a decorator (`@`). It automatically handles starting and stopping the timer.

  Parameters:
  - `name (str)`: The identifier for the scope.

* `ScopeTimer.begin(name: str)`

  Manually starts a timer scope. This is useful in situations where a context manager or decorator cannot be used. Each `begin()` call must be paired with a corresponding `end()` call.

  Parameters:
  - `name (str)`: The identifier for the scope to start.

* `ScopeTimer.end(name: str)`

  Manually stops the currently active timer scope.

  Parameters:
  - `name (str)`: The identifier for the scope to end. Must match the name of the currently active scope.

### Reporting Methods

* `ScopeTimer.summarize(time_unit="auto", precision="auto", divider="rule", verbose=False)`

  Prints a formatted summary of timing results to the console.

  Parameters:
  - `time_unit (str)`: The display unit for time. Can be `'auto'`, `'s'`, `'ms'`, or `'us'`. Defaults to `'auto'`.
  - `precision (int | str)`: The number of decimal places for time values. Defaults to `'auto'`.
  - `divider (str)`: The style of the separator between root scopes. Can be `'rule'` or `'blank'`. Defaults to `'rule'`.
  - `verbose (bool)`: If True, displays detailed statistics (min, max, avg, var). Defaults to `False`.

* `ScopeTimer.save_txt(file_path, **kwargs)`

  Saves a summary of timing results as a plain text file.

  Parameters:
  - `file_path (str | Path)`: The path to the output file.
  - `**kwargs`: Accepts the same arguments as `summarize()` (`time_unit`, `precision`, `verbose`).

* `ScopeTimer.save_html(file_path, **kwargs)`

  Saves a summary of timing results as a themed HTML file.

  Parameters:
  - `file_path (str | Path)`: The path to the output file.
  - `**kwargs`: Accepts the same arguments as `summarize()` (`time_unit`, `precision`, `verbose`).

### Utility Methods

* `ScopeTimer.reset()`

  Resets all recorded timer data, clearing all scopes and measurements. Use this to start a fresh set of measurements within the same process.


## License

This project is licensed under the MIT License.
