"""Run a lightweight project health check.

This script is useful before committing changes. It runs the sanity tests,
executes the default simulation, regenerates report inputs, and verifies that
the final result and portfolio artifacts exist.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import re
import subprocess
import sys


REQUIRED_ARTIFACTS = [
    Path("README.md"),
    Path("LICENSE"),
    Path("docs/experiment_plan_v2.md"),
    Path("docs/model_assumptions.md"),
    Path("docs/portfolio_summary.md"),
    Path("report/project_report_final.md"),
    Path("report/references.md"),
    Path("results/data/main_summary.csv"),
    Path("results/data/default_run_metadata.json"),
    Path("results/data/file_size_variability_experiment.csv"),
    Path("results/data/file_size_variability_experiment_metadata.json"),
    Path("results/data/key_findings.md"),
    Path("results/data/multi_seed_cache_capacity_summary.csv"),
    Path("results/data/multi_seed_cache_capacity_metadata.json"),
    Path("results/data/spatial_locality_experiment.csv"),
    Path("results/data/spatial_locality_experiment_metadata.json"),
    Path("results/data/user_activity_experiment.csv"),
    Path("results/data/user_activity_experiment_metadata.json"),
    Path("results/data/wireless_channel_experiment.csv"),
    Path("results/data/wireless_channel_experiment_metadata.json"),
    Path("results/data/mab_comparison_experiment.csv"),
    Path("results/data/mab_comparison_diagnostics.csv"),
    Path("results/data/mab_comparison_metadata.json"),
    Path("results/data/multi_seed_v2_raw.csv"),
    Path("results/data/multi_seed_v2_summary.csv"),
    Path("results/data/multi_seed_v2_mab_diagnostics.csv"),
    Path("results/data/multi_seed_v2_mab_diagnostics_summary.csv"),
    Path("results/data/multi_seed_v2_metadata.json"),
    Path("results/data/final_v2_figures_metadata.json"),
    Path("results/figures/network_topology.png"),
    Path("results/figures/content_popularity_zipf.png"),
    Path("results/figures/main_average_latency.png"),
    Path("results/figures/main_p95_latency.png"),
    Path("results/figures/main_cache_hit_ratio.png"),
    Path("results/figures/main_backhaul_traffic.png"),
    Path("results/figures/main_wireless_rate.png"),
    Path("results/figures/main_bandwidth_fairness.png"),
    Path("results/figures/main_latency_breakdown.png"),
    Path("results/figures/latency_vs_file_size_variability.png"),
    Path("results/figures/backhaul_vs_file_size_variability.png"),
    Path("results/figures/latency_vs_spatial_locality.png"),
    Path("results/figures/latency_vs_user_activity.png"),
    Path("results/figures/fairness_vs_user_activity.png"),
    Path("results/figures/latency_vs_path_loss_exponent.png"),
    Path("results/figures/rate_vs_path_loss_exponent.png"),
    Path("results/figures/mab_comparison_average_latency.png"),
    Path("results/figures/mab_comparison_cache_hit_ratio.png"),
    Path("results/figures/v2_strategy_latency_mean_std.png"),
    Path("results/figures/v2_strategy_hit_ratio_mean_std.png"),
    Path("results/figures/v2_paired_latency_vs_random.png"),
    Path("docs/figures/v2_strategy_latency_mean_std.png"),
    Path("docs/figures/v2_strategy_hit_ratio_mean_std.png"),
    Path("docs/figures/v2_paired_latency_vs_random.png"),
    Path("report/generated_results.md"),
]

MARKDOWN_DOCUMENTS = (
    Path("README.md"),
    Path("docs/portfolio_summary.md"),
    Path("report/project_report_final.md"),
)
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
EXTERNAL_LINK_PREFIXES = ("http://", "https://", "mailto:", "#")


def _run_step(description: str, command: list[str]) -> None:
    print(f"\n[check] {description}", flush=True)
    subprocess.run(command, check=True)


def _verify_artifacts() -> None:
    missing = [
        str(path)
        for path in REQUIRED_ARTIFACTS
        if not path.exists() or path.stat().st_size == 0
    ]
    if missing:
        missing_list = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing expected artifact files:\n{missing_list}")

    print(
        f"\n[check] Verified {len(REQUIRED_ARTIFACTS)} artifact files",
        flush=True,
    )


def _verify_markdown_links(document_paths: Iterable[Path]) -> None:
    """Verify that local links and images in key Markdown files resolve."""

    missing: list[str] = []
    checked_documents = 0

    for document_path in document_paths:
        checked_documents += 1
        content = document_path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_PATTERN.finditer(content):
            target = match.group(1).strip()
            if not target or target.startswith(EXTERNAL_LINK_PREFIXES):
                continue

            path_without_fragment = target.split("#", maxsplit=1)[0]
            if not path_without_fragment:
                continue

            linked_path = document_path.parent / path_without_fragment
            if not linked_path.exists():
                missing.append(f"{document_path}: {target}")

    if missing:
        missing_list = "\n".join(f"- {item}" for item in missing)
        raise FileNotFoundError(
            f"Missing local Markdown targets:\n{missing_list}"
        )

    print(
        f"[check] Verified local links in {checked_documents} Markdown files",
        flush=True,
    )


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
        "Running file-size variability experiment",
        [python, "experiments/run_file_size_variability_experiment.py"],
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
        "Running wireless channel sensitivity experiment",
        [python, "experiments/run_wireless_channel_experiment.py"],
    )
    _run_step(
        "Running held-out MAB caching comparison",
        [python, "experiments/run_mab_comparison_experiment.py"],
    )
    _run_step(
        "Running multi-seed v2 strategy summary",
        [python, "experiments/run_multi_seed_v2_experiment.py"],
    )
    _run_step(
        "Generating final v2 figures",
        [python, "generate_final_figures.py"],
    )
    _run_step(
        "Generating key findings summary",
        [python, "summarize_results.py"],
    )
    _run_step(
        "Generating report assets",
        [python, "generate_report_assets.py"],
    )
    _verify_artifacts()
    _verify_markdown_links(MARKDOWN_DOCUMENTS)

    print("\nProject health check completed successfully.", flush=True)


if __name__ == "__main__":
    main()
