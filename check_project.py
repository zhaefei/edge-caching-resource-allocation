"""Run a lightweight project health check.

This script is useful before committing changes. It runs the sanity tests,
executes the default simulation, and regenerates the short result summary.
"""

from __future__ import annotations

import subprocess
import sys


def _run_step(description: str, command: list[str]) -> None:
    print(f"\n[check] {description}", flush=True)
    subprocess.run(command, check=True)


def main() -> None:
    python = sys.executable

    _run_step(
        "Running sanity tests",
        [python, "-m", "unittest", "discover", "-s", "tests"],
    )
    _run_step(
        "Running default simulation",
        [python, "main.py"],
    )
    _run_step(
        "Generating key findings summary",
        [python, "summarize_results.py"],
    )

    print("\nProject health check completed successfully.", flush=True)


if __name__ == "__main__":
    main()
