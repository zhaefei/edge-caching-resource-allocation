"""Run a cache capacity sweep over multiple random seeds.

This experiment gives a more reliable view of performance trends than a single
random topology/request trace. It reports both mean and standard deviation for
the main metrics.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import SimulationConfig
from src.simulation import run_strategy_comparison
from src.visualization import ensure_results_dirs, plot_experiment_mean_std


def main() -> None:
    base_config = SimulationConfig()
    cache_capacities = [2, 4, 6, 8, 10, 12, 15, 20]
    seeds = [11, 22, 33, 44, 55]
    frames = []

    for seed in seeds:
        for capacity in cache_capacities:
            config = replace(
                base_config,
                seed=seed,
                cache_capacity=capacity,
            )
            results = run_strategy_comparison(config)
            results["seed"] = seed
            results["cache_capacity"] = capacity
            frames.append(results)

    raw_results = pd.concat(frames, ignore_index=True)
    summary = (
        raw_results.groupby(["strategy", "cache_capacity"], as_index=False)
        .agg(
            avg_latency_ms_mean=("avg_latency_ms", "mean"),
            avg_latency_ms_std=("avg_latency_ms", "std"),
            cache_hit_ratio_mean=("cache_hit_ratio", "mean"),
            cache_hit_ratio_std=("cache_hit_ratio", "std"),
            backhaul_load_ratio_mean=("backhaul_load_ratio", "mean"),
            backhaul_load_ratio_std=("backhaul_load_ratio", "std"),
            avg_wireless_rate_mbps_mean=("avg_wireless_rate_mbps", "mean"),
            avg_wireless_rate_mbps_std=("avg_wireless_rate_mbps", "std"),
        )
        .reset_index(drop=True)
    )

    data_dir, figure_dir = ensure_results_dirs(base_config.results_dir)
    raw_results.to_csv(
        data_dir / "multi_seed_cache_capacity_raw.csv",
        index=False,
    )
    summary.to_csv(
        data_dir / "multi_seed_cache_capacity_summary.csv",
        index=False,
    )

    plot_experiment_mean_std(
        summary,
        x_column="cache_capacity",
        mean_column="avg_latency_ms_mean",
        std_column="avg_latency_ms_std",
        ylabel="Average Latency (ms)",
        title="Latency vs Cache Capacity Averaged Over Random Seeds",
        output_path=figure_dir / "multi_seed_latency_vs_cache_capacity.png",
    )
    plot_experiment_mean_std(
        summary,
        x_column="cache_capacity",
        mean_column="cache_hit_ratio_mean",
        std_column="cache_hit_ratio_std",
        ylabel="Cache Hit Ratio",
        title="Cache Hit Ratio vs Cache Capacity Averaged Over Random Seeds",
        output_path=figure_dir / "multi_seed_hit_ratio_vs_cache_capacity.png",
    )

    print("Multi-seed cache capacity experiment completed.")
    print(f"Saved raw data to {data_dir / 'multi_seed_cache_capacity_raw.csv'}")
    print(f"Saved summary to {data_dir / 'multi_seed_cache_capacity_summary.csv'}")


if __name__ == "__main__":
    main()
