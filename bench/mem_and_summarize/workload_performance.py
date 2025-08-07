import matplotlib.pyplot as plt
import matplotlib.ticker as mticker # Import the ticker module
from pympler.asizeof import asizeof
from scope_timer import ScopeTimer
import time
import sys
import io

def format_bytes(byte_size, pos=None): # Add pos argument for the formatter
    """Converts bytes to a human-readable string (KB or MB)."""
    if byte_size > 1024 * 1024:
        return f"{byte_size / (1024 * 1024):.2f} MB"
    if byte_size > 1024:
        return f"{byte_size / 1024:.2f} KB"
    return f"{byte_size} Bytes"

def run_and_measure_pipeline(n_iterations, n_predictions=20):
    """
    Simulates a realistic pipeline, then measures final memory and
    the performance of the summarize() function.
    """
    ScopeTimer.reset()

    # Run the pipeline simulation n_iterations times
    for _ in range(n_iterations):
        with ScopeTimer.profile_block("pipeline_run"):
            # Stage 1: Preprocess (2 sub-scopes)
            with ScopeTimer.profile_block("preprocess"):
                with ScopeTimer.profile_block("load_data"):
                    pass
                with ScopeTimer.profile_block("clean_data"):
                    pass

            # Stage 2: Compute (includes a loop for sub-nodes)
            with ScopeTimer.profile_block("compute"):
                with ScopeTimer.profile_block("feature_extraction"):
                    pass
                # Loop to simulate multiple low-level operations
                for j in range(n_predictions):
                    with ScopeTimer.profile_block(f"prediction_{j}"):
                        pass

            # Stage 3: Postprocess (1 sub-scope)
            with ScopeTimer.profile_block("postprocess"):
                with ScopeTimer.profile_block("save_results"):
                    pass

    # Measure execution time and final memory impact of summarize()
    # Suppress console output during timing
    original_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()

    start_time = time.perf_counter()
    ScopeTimer.summarize() # This calculates stats internally
    end_time = time.perf_counter()

    sys.stdout = original_stdout # Restore console output

    summarize_duration = end_time - start_time
    mem_after = asizeof(ScopeTimer._local)

    return mem_after, summarize_duration

def main():
    """Main function to run the benchmark and plot the results."""
    print("Running final performance benchmark... This may take a moment.")

    iterations_list = []
    mem_after_list = []
    summarize_time_list = []

    # Scale the number of pipeline runs
    for n_iterations in range(10, 4011, 200):
        mem_after, summarize_time = run_and_measure_pipeline(n_iterations)
        iterations_list.append(n_iterations)
        mem_after_list.append(mem_after)
        summarize_time_list.append(summarize_time)
        print(f"{n_iterations=}, {mem_after=}, {summarize_time=}")

    print("Generating plot...")
    # --- Plotting with xkcd style ---
    with plt.xkcd():
        plt.rcParams['font.family'] = 'Comic Neue'
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('ScopeTimer Performance Analysis', fontsize=16)

        # Plot 1: Memory Usage (After summarize() only)
        ax1.plot(iterations_list, mem_after_list, 'r')
        ax1.set_title('ScopeTimer Memory Usage (after summarize())')
        ax1.set_xlabel('Number of Pipeline Runs (Iterations)')
        ax1.set_ylabel('Memory Usage') # Removed (bytes) from label

        # Apply the custom formatter to the Y-axis
        ax1.yaxis.set_major_formatter(mticker.FuncFormatter(format_bytes))

        # Plot 2: summarize() Execution Time
        ax2.plot(iterations_list, summarize_time_list, 'g')
        ax2.set_title('summarize() Execution Time')
        ax2.set_xlabel('Number of Pipeline Runs (Iterations)')
        ax2.set_ylabel('Execution Time (seconds)')

        fig.tight_layout(rect=(0, 0.03, 1, 0.95))

        output_filename = "scope_timer_performance.png"
        plt.savefig(output_filename)
        print(f"Plot saved to {output_filename}")
        plt.show()

if __name__ == "__main__":
    main()
