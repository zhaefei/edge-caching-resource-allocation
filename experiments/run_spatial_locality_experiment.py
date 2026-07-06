"""Sweep spatial locality strength to study when local caching is valuable."""

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
    locality_strengths = [0.0, 0.2, 0.4, 0.6, 0.8]
    frames = []

    for locality_strength in locality_strengths:
        config = replace(
            base_config,
            spatial_locality_strength=locality_strength,
        )
        results = run_strategy_comparison(config)
        results["spatial_locality_strength"] = locality_strength
        frames.append(results)

    all_results = pd.concat(frames, ignore_index=True)
    data_dir, figure_dir = ensure_results_dirs(base_config.results_dir)
    all_results.to_csv(data_dir / "spatial_locality_experiment.csv", index=False)

    plot_experiment_line(
        all_results,
        x_column="spatial_locality_strength",
        y_column="avg_latency_ms",
        ylabel="Average Latency (ms)",
        title="Latency vs Spatial Locality Strength",
        output_path=figure_dir / "latency_vs_spatial_locality.png",
        xlabel="Spatial locality strength",
    )
    plot_experiment_line(
        all_results,
        x_column="spatial_locality_strength",
        y_column="cache_hit_ratio",
        ylabel="Cache Hit Ratio",
        title="Cache Hit Ratio vs Spatial Locality Strength",
        output_path=figure_dir / "hit_ratio_vs_spatial_locality.png",
        xlabel="Spatial locality strength",
    )

    print("Spatial locality experiment completed.")
    print(f"Saved data to {data_dir / 'spatial_locality_experiment.csv'}")


if __name__ == "__main__":
    main()
