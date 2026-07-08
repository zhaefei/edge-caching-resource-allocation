"""Sweep user activity skew to study demand-aware bandwidth allocation."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import SimulationConfig
from src.reproducibility import write_run_metadata
from src.simulation import run_strategy_comparison
from src.visualization import ensure_results_dirs, plot_experiment_line


def main() -> None:
    base_config = SimulationConfig()
    activity_alpha_values = [0.0, 0.2, 0.4, 0.8, 1.2]
    frames = []

    for user_activity_alpha in activity_alpha_values:
        config = replace(base_config, user_activity_alpha=user_activity_alpha)
        results = run_strategy_comparison(config)
        results["user_activity_alpha"] = user_activity_alpha
        frames.append(results)

    all_results = pd.concat(frames, ignore_index=True)
    data_dir, figure_dir = ensure_results_dirs(base_config.results_dir)
    all_results.to_csv(data_dir / "user_activity_experiment.csv", index=False)
    write_run_metadata(
        base_config,
        data_dir / "user_activity_experiment_metadata.json",
        run_name="user_activity_experiment",
        extra_metadata={
            "sweep_parameter": "user_activity_alpha",
            "sweep_values": activity_alpha_values,
            "output_files": [
                "results/data/user_activity_experiment.csv",
                "results/figures/latency_vs_user_activity.png",
                "results/figures/fairness_vs_user_activity.png",
            ],
        },
    )

    plot_experiment_line(
        all_results,
        x_column="user_activity_alpha",
        y_column="avg_latency_ms",
        ylabel="Average Latency (ms)",
        title="Latency vs User Activity Skew",
        output_path=figure_dir / "latency_vs_user_activity.png",
        xlabel="User activity Zipf alpha",
    )
    plot_experiment_line(
        all_results,
        x_column="user_activity_alpha",
        y_column="bandwidth_fairness_index",
        ylabel="Jain's Bandwidth Fairness Index",
        title="Bandwidth Fairness vs User Activity Skew",
        output_path=figure_dir / "fairness_vs_user_activity.png",
        xlabel="User activity Zipf alpha",
    )

    print("User activity skew experiment completed.")
    print(f"Saved data to {data_dir / 'user_activity_experiment.csv'}")


if __name__ == "__main__":
    main()
