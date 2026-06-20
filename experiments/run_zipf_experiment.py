"""Sweep the Zipf popularity parameter for content requests."""

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
    zipf_alphas = [0.4, 0.6, 0.8, 1.0, 1.2, 1.5]
    frames = []

    for alpha in zipf_alphas:
        config = replace(base_config, zipf_alpha=alpha)
        results = run_strategy_comparison(config)
        results["zipf_alpha"] = alpha
        frames.append(results)

    all_results = pd.concat(frames, ignore_index=True)
    data_dir, figure_dir = ensure_results_dirs(base_config.results_dir)
    all_results.to_csv(data_dir / "zipf_experiment.csv", index=False)

    plot_experiment_line(
        all_results,
        x_column="zipf_alpha",
        y_column="avg_latency_ms",
        ylabel="Average Latency (ms)",
        title="Latency vs Zipf Popularity Parameter",
        output_path=figure_dir / "latency_vs_zipf_alpha.png",
    )
    plot_experiment_line(
        all_results,
        x_column="zipf_alpha",
        y_column="cache_hit_ratio",
        ylabel="Cache Hit Ratio",
        title="Cache Hit Ratio vs Zipf Popularity Parameter",
        output_path=figure_dir / "hit_ratio_vs_zipf_alpha.png",
    )

    print("Zipf experiment completed.")
    print(f"Saved data to {data_dir / 'zipf_experiment.csv'}")


if __name__ == "__main__":
    main()
