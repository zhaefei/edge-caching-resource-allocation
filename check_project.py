"""Run a lightweight project health check.

This script is useful before committing changes. It runs the sanity tests,
executes the default simulation, regenerates report inputs, and verifies that
key output artifacts were created.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


REQUIRED_OUTPUTS = [
    Path("results/data/main_summary.csv"),
    Path("results/data/default_run_metadata.json"),
    Path("results/data/key_findings.md"),
    Path("results/data/multi_seed_cache_capacity_summary.csv"),
    Path("results/data/multi_seed_cache_capacity_metadata.json"),
    Path("results/data/spatial_locality_experiment.csv"),
    Path("results/data/spatial_locality_experiment_metadata.json"),
    Path("results/data/user_activity_experiment.csv"),
    Path("results/data/user_activity_experiment_metadata.json"),
    Path("results/figures/network_topology.png"),
    Path("results/figures/content_popularity_zipf.png"),
    Path("results/figures/main_average_latency.png"),
    Path("results/figures/main_p95_latency.png"),
    Path("results/figures/main_cache_hit_ratio.png"),
    Path("results/figures/main_backhaul_traffic.png"),
    Path("results/figures/main_wireless_rate.png"),
    Path("results/figures/main_bandwidth_fairness.png"),
    Path("results/figures/main_latency_breakdown.png"),
    Path("results/figures/latency_vs_spatial_locality.png"),
    Path("results/figures/latency_vs_user_activity.png"),
    Path("results/figures/fairness_vs_user_activity.png"),
    Path("report/generated_results.md"),
]


def _run_step(description: str, command: list[str]) -> None:
    print(f"\n[check] {description}", flush=True)
    subprocess.run(command, check=True)


def _verify_outputs() -> None:
    missing = [
        str(path)
        for path in REQUIRED_OUTPUTS
        if not path.exists() or path.stat().st_size == 0
    ]
    if missing:
        missing_list = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing expected output files:\n{missing_list}")

    print(f"\n[check] Verified {len(REQUIRED_OUTPUTS)} output files", flush=True)


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
        "Running multi-seed cache capacity summary",
        [python, "experiments/run_multi_seed_cache_capacity_experiment.py"],
    )
    _run_step(
        "Running spatial locality sensitivity experiment",
        [python, "experiments/run_spatial_locality_experiment.py"],
    )
    _run_step(
        "Running user activity skew experiment",
        [python, "experiments/run_user_activity_experiment.py"],
    )
    _run_step(
        "Generating key findings summary",
        [python, "summarize_results.py"],
    )
    _run_step(
        "Generating report assets",
        [python, "generate_report_assets.py"],
    )
    _verify_outputs()

    print("\nProject health check completed successfully.", flush=True)


if __name__ == "__main__":
    main()
