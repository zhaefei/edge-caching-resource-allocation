"""Compare UCB-style MAB caching with fixed-cache baselines fairly."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import SimulationConfig
from src.reproducibility import write_run_metadata
from src.simulation import (
    MAB_COMPARISON_STRATEGIES,
    MABComparisonResult,
    run_mab_strategy_comparison,
)
from src.visualization import ensure_results_dirs, plot_metric_bar


def build_mab_diagnostics_record(
    config: SimulationConfig,
    comparison: MABComparisonResult,
) -> dict[str, int | float]:
    """Create a compact, CSV-friendly record of MAB learning behavior."""

    mab_cache = comparison.final_caches[MAB_COMPARISON_STRATEGIES[-1]]
    cache_usage_mbits = [
        sum(
            float(comparison.file_sizes_mbits[file_id])
            for file_id in cached_files
        )
        for cached_files in mab_cache.values()
    ]
    mean_cache_utilization = (
        sum(cache_usage_mbits)
        / len(cache_usage_mbits)
        / config.cache_budget_mbits
        if cache_usage_mbits and config.cache_budget_mbits > 0.0
        else 0.0
    )
    total_requests = (
        comparison.training_request_count + comparison.evaluation_request_count
    )

    return {
        "simulation_seed": int(config.seed),
        "mab_policy_seed": int(config.seed + config.mab_seed_offset),
        "configured_training_fraction": float(config.mab_training_fraction),
        "actual_training_fraction": float(
            comparison.training_request_count / total_requests
        ),
        "training_request_count": int(comparison.training_request_count),
        "evaluation_request_count": int(comparison.evaluation_request_count),
        "mab_update_interval": int(config.mab_update_interval),
        "mab_exploration_weight": float(config.mab_exploration_weight),
        "completed_epochs": int(comparison.mab_diagnostics.completed_epochs),
        "explored_arm_fraction": float(
            comparison.mab_diagnostics.explored_arm_fraction
        ),
        "selected_arm_updates": int(
            comparison.mab_diagnostics.selection_counts.sum()
        ),
        "final_cached_file_count_total": int(
            sum(len(cached_files) for cached_files in mab_cache.values())
        ),
        "mean_final_cache_utilization": float(mean_cache_utilization),
    }


def main() -> None:
    config = SimulationConfig()
    comparison = run_mab_strategy_comparison(config)
    diagnostics = build_mab_diagnostics_record(config, comparison)

    data_dir, figure_dir = ensure_results_dirs(config.results_dir)
    metrics_path = data_dir / "mab_comparison_experiment.csv"
    diagnostics_path = data_dir / "mab_comparison_diagnostics.csv"
    metadata_path = data_dir / "mab_comparison_metadata.json"
    comparison.metrics.to_csv(metrics_path, index=False)
    pd.DataFrame([diagnostics]).to_csv(diagnostics_path, index=False)

    output_files = [
        "results/data/mab_comparison_experiment.csv",
        "results/data/mab_comparison_diagnostics.csv",
        "results/data/mab_comparison_metadata.json",
        "results/figures/mab_comparison_average_latency.png",
        "results/figures/mab_comparison_cache_hit_ratio.png",
    ]
    write_run_metadata(
        config,
        metadata_path,
        run_name="mab_comparison_experiment",
        extra_metadata={
            "protocol": "chronological training prefix and held-out evaluation suffix",
            "bandwidth_allocation": "equal for every caching strategy",
            "strategy_labels": list(MAB_COMPARISON_STRATEGIES),
            "mab_diagnostics": diagnostics,
            "output_files": output_files,
        },
    )

    plot_metric_bar(
        comparison.metrics,
        metric="avg_latency_ms",
        ylabel="Average Latency (ms)",
        output_path=figure_dir / "mab_comparison_average_latency.png",
        title="Held-Out Latency Comparison for Caching Policies",
    )
    plot_metric_bar(
        comparison.metrics,
        metric="cache_hit_ratio",
        ylabel="Cache Hit Ratio",
        output_path=figure_dir / "mab_comparison_cache_hit_ratio.png",
        title="Held-Out Cache Hit Ratio Comparison",
    )

    print("MAB caching comparison experiment completed.")
    print(f"Saved metrics to {metrics_path}")
    print(f"Saved diagnostics to {diagnostics_path}")


if __name__ == "__main__":
    main()
