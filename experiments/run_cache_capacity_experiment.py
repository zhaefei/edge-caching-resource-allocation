"""Sweep cache capacity and compare caching/resource allocation strategies."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import SimulationConfig
from src.simulation import run_strategy_comparison
from src.visualization import ensure_results_dirs, plot_experiment_line


def main() -> None:
    base_config = SimulationConfig()
    cache_capacities = [2, 4, 6, 8, 10, 12, 15, 20]
    frames = []

    for capacity in cache_capacities:
        config = replace(base_config, cache_capacity=capacity)
        results = run_strategy_comparison(config)
        results["cache_capacity"] = capacity
        frames.append(results)

    all_results = pd.concat(frames, ignore_index=True)
    data_dir, figure_dir = ensure_results_dirs(base_config.results_dir)
    all_results.to_csv(data_dir / "cache_capacity_experiment.csv", index=False)

    plot_experiment_line(
        all_results,
        x_column="cache_capacity",
        y_column="avg_latency_ms",
        ylabel="Average Latency (ms)",
        title="Latency vs Cache Capacity",
        output_path=figure_dir / "latency_vs_cache_capacity.png",
    )
    plot_experiment_line(
        all_results,
        x_column="cache_capacity",
        y_column="cache_hit_ratio",
        ylabel="Cache Hit Ratio",
        title="Cache Hit Ratio vs Cache Capacity",
        output_path=figure_dir / "hit_ratio_vs_cache_capacity.png",
    )

    print("Cache capacity experiment completed.")
    print(f"Saved data to {data_dir / 'cache_capacity_experiment.csv'}")


if __name__ == "__main__":
    main()
