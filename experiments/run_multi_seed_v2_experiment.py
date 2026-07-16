"""Repeat the final held-out v2 caching comparison over fixed random seeds."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import SimulationConfig
from experiments.run_mab_comparison_experiment import (
    build_mab_diagnostics_record,
)
from src.reproducibility import write_run_metadata
from src.simulation import MAB_COMPARISON_STRATEGIES, run_mab_strategy_comparison
from src.visualization import ensure_results_dirs


DEFAULT_V2_SEEDS = (11, 22, 33, 44, 55)
PAIR_REFERENCE_STRATEGY = MAB_COMPARISON_STRATEGIES[0]
PAIRED_METRICS = (
    "avg_latency_ms",
    "p95_latency_ms",
    "cache_hit_ratio",
    "backhaul_load_ratio",
)


@dataclass(frozen=True)
class MultiSeedV2Result:
    """Raw and summarized metrics from the multi-seed v2 comparison."""

    raw_metrics: pd.DataFrame
    summary_metrics: pd.DataFrame
    raw_mab_diagnostics: pd.DataFrame
    summary_mab_diagnostics: pd.DataFrame


def run_multi_seed_v2_experiment(
    base_config: SimulationConfig,
    seeds: Sequence[int] = DEFAULT_V2_SEEDS,
) -> MultiSeedV2Result:
    """Run the held-out v2 strategy set and report mean/std across seeds."""

    validated_seeds = _validate_seeds(seeds)
    metric_frames = []
    diagnostic_records = []

    for seed in validated_seeds:
        config = replace(base_config, seed=seed)
        comparison = run_mab_strategy_comparison(config)

        seed_metrics = comparison.metrics.copy()
        seed_metrics.insert(1, "seed", seed)
        metric_frames.append(seed_metrics)
        diagnostic_records.append(build_mab_diagnostics_record(config, comparison))

    raw_metrics = _add_paired_random_differences(
        pd.concat(metric_frames, ignore_index=True)
    )
    raw_mab_diagnostics = pd.DataFrame(diagnostic_records)
    return MultiSeedV2Result(
        raw_metrics=raw_metrics,
        summary_metrics=_summarize_metrics(raw_metrics),
        raw_mab_diagnostics=raw_mab_diagnostics,
        summary_mab_diagnostics=_summarize_mab_diagnostics(
            raw_mab_diagnostics
        ),
    )


def _validate_seeds(seeds: Sequence[int]) -> tuple[int, ...]:
    """Require at least two distinct non-negative integer seeds."""

    seeds = tuple(seeds)
    if len(seeds) < 2:
        raise ValueError("multi-seed v2 evaluation requires at least two seeds")
    if any(
        isinstance(seed, (bool, np.bool_))
        or not isinstance(seed, (int, np.integer))
        or seed < 0
        for seed in seeds
    ):
        raise ValueError("seeds must be non-negative integers")
    normalized_seeds = tuple(int(seed) for seed in seeds)
    if len(set(normalized_seeds)) != len(normalized_seeds):
        raise ValueError("multi-seed v2 evaluation requires distinct seeds")
    return normalized_seeds


def _add_paired_random_differences(raw_metrics: pd.DataFrame) -> pd.DataFrame:
    """Add within-seed differences relative to the random-cache baseline."""

    paired_metrics = raw_metrics.copy()
    reference_rows = paired_metrics.loc[
        paired_metrics["strategy"] == PAIR_REFERENCE_STRATEGY
    ].set_index("seed")
    expected_seeds = set(paired_metrics["seed"])
    if (
        reference_rows.index.has_duplicates
        or set(reference_rows.index) != expected_seeds
    ):
        raise ValueError("each seed must contain exactly one random-cache baseline")

    for metric in PAIRED_METRICS:
        reference_values = paired_metrics["seed"].map(reference_rows[metric])
        paired_metrics[f"{metric}_delta_vs_random"] = (
            paired_metrics[metric] - reference_values
        )
    return paired_metrics


def _summarize_metrics(raw_metrics: pd.DataFrame) -> pd.DataFrame:
    """Aggregate portfolio-facing network metrics by caching strategy."""

    return (
        raw_metrics.groupby(
            ["strategy", "cache_information", "bandwidth_allocation"],
            as_index=False,
            sort=False,
        )
        .agg(
            seed_count=("seed", "nunique"),
            avg_latency_ms_mean=("avg_latency_ms", "mean"),
            avg_latency_ms_std=("avg_latency_ms", "std"),
            median_latency_ms_mean=("median_latency_ms", "mean"),
            median_latency_ms_std=("median_latency_ms", "std"),
            p95_latency_ms_mean=("p95_latency_ms", "mean"),
            p95_latency_ms_std=("p95_latency_ms", "std"),
            cache_hit_ratio_mean=("cache_hit_ratio", "mean"),
            cache_hit_ratio_std=("cache_hit_ratio", "std"),
            backhaul_traffic_mbits_mean=("backhaul_traffic_mbits", "mean"),
            backhaul_traffic_mbits_std=("backhaul_traffic_mbits", "std"),
            backhaul_load_ratio_mean=("backhaul_load_ratio", "mean"),
            backhaul_load_ratio_std=("backhaul_load_ratio", "std"),
            avg_wireless_rate_mbps_mean=("avg_wireless_rate_mbps", "mean"),
            avg_wireless_rate_mbps_std=("avg_wireless_rate_mbps", "std"),
            avg_latency_ms_delta_vs_random_mean=(
                "avg_latency_ms_delta_vs_random",
                "mean",
            ),
            avg_latency_ms_delta_vs_random_std=(
                "avg_latency_ms_delta_vs_random",
                "std",
            ),
            p95_latency_ms_delta_vs_random_mean=(
                "p95_latency_ms_delta_vs_random",
                "mean",
            ),
            p95_latency_ms_delta_vs_random_std=(
                "p95_latency_ms_delta_vs_random",
                "std",
            ),
            cache_hit_ratio_delta_vs_random_mean=(
                "cache_hit_ratio_delta_vs_random",
                "mean",
            ),
            cache_hit_ratio_delta_vs_random_std=(
                "cache_hit_ratio_delta_vs_random",
                "std",
            ),
            backhaul_load_ratio_delta_vs_random_mean=(
                "backhaul_load_ratio_delta_vs_random",
                "mean",
            ),
            backhaul_load_ratio_delta_vs_random_std=(
                "backhaul_load_ratio_delta_vs_random",
                "std",
            ),
        )
        .reset_index(drop=True)
    )


def _summarize_mab_diagnostics(
    raw_diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize learning coverage and cache usage across random seeds."""

    return pd.DataFrame(
        [
            {
                "seed_count": int(raw_diagnostics["simulation_seed"].nunique()),
                "completed_epochs_mean": float(
                    raw_diagnostics["completed_epochs"].mean()
                ),
                "completed_epochs_std": float(
                    raw_diagnostics["completed_epochs"].std(ddof=1)
                ),
                "explored_arm_fraction_mean": float(
                    raw_diagnostics["explored_arm_fraction"].mean()
                ),
                "explored_arm_fraction_std": float(
                    raw_diagnostics["explored_arm_fraction"].std(ddof=1)
                ),
                "selected_arm_updates_mean": float(
                    raw_diagnostics["selected_arm_updates"].mean()
                ),
                "selected_arm_updates_std": float(
                    raw_diagnostics["selected_arm_updates"].std(ddof=1)
                ),
                "mean_final_cache_utilization_mean": float(
                    raw_diagnostics["mean_final_cache_utilization"].mean()
                ),
                "mean_final_cache_utilization_std": float(
                    raw_diagnostics["mean_final_cache_utilization"].std(ddof=1)
                ),
            }
        ]
    )


def main() -> None:
    base_config = SimulationConfig()
    result = run_multi_seed_v2_experiment(base_config)
    data_dir, _ = ensure_results_dirs(base_config.results_dir)

    raw_path = data_dir / "multi_seed_v2_raw.csv"
    summary_path = data_dir / "multi_seed_v2_summary.csv"
    diagnostics_path = data_dir / "multi_seed_v2_mab_diagnostics.csv"
    diagnostics_summary_path = (
        data_dir / "multi_seed_v2_mab_diagnostics_summary.csv"
    )
    metadata_path = data_dir / "multi_seed_v2_metadata.json"

    result.raw_metrics.to_csv(raw_path, index=False)
    result.summary_metrics.to_csv(summary_path, index=False)
    result.raw_mab_diagnostics.to_csv(diagnostics_path, index=False)
    result.summary_mab_diagnostics.to_csv(
        diagnostics_summary_path,
        index=False,
    )
    write_run_metadata(
        base_config,
        metadata_path,
        run_name="multi_seed_v2_experiment",
        extra_metadata={
            "seeds": list(DEFAULT_V2_SEEDS),
            "seed_count": len(DEFAULT_V2_SEEDS),
            "protocol": "60/40 chronological held-out caching comparison",
            "standard_deviation": "sample standard deviation (ddof=1)",
            "paired_reference_strategy": PAIR_REFERENCE_STRATEGY,
            "paired_difference_definition": (
                "strategy metric minus same-seed reference metric"
            ),
            "strategy_labels": list(MAB_COMPARISON_STRATEGIES),
            "output_files": [
                "results/data/multi_seed_v2_raw.csv",
                "results/data/multi_seed_v2_summary.csv",
                "results/data/multi_seed_v2_mab_diagnostics.csv",
                "results/data/multi_seed_v2_mab_diagnostics_summary.csv",
                "results/data/multi_seed_v2_metadata.json",
            ],
        },
    )

    print("Multi-seed v2 experiment completed.")
    print(f"Saved raw metrics to {raw_path}")
    print(f"Saved summary metrics to {summary_path}")


if __name__ == "__main__":
    main()
