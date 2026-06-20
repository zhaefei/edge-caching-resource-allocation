"""Sweep the number of users in the wireless edge network."""

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
    user_counts = [25, 50, 100, 150, 200]
    frames = []

    for num_users in user_counts:
        config = replace(base_config, num_users=num_users)
        results = run_strategy_comparison(config)
        results["num_users"] = num_users
        frames.append(results)

    all_results = pd.concat(frames, ignore_index=True)
    data_dir, figure_dir = ensure_results_dirs(base_config.results_dir)
    all_results.to_csv(data_dir / "user_density_experiment.csv", index=False)

    plot_experiment_line(
        all_results,
        x_column="num_users",
        y_column="avg_latency_ms",
        ylabel="Average Latency (ms)",
        title="Latency vs Number of Users",
        output_path=figure_dir / "latency_vs_num_users.png",
    )
    plot_experiment_line(
        all_results,
        x_column="num_users",
        y_column="avg_wireless_rate_mbps",
        ylabel="Average Wireless Rate (Mbps)",
        title="Wireless Rate vs Number of Users",
        output_path=figure_dir / "rate_vs_num_users.png",
    )

    print("User density experiment completed.")
    print(f"Saved data to {data_dir / 'user_density_experiment.csv'}")


if __name__ == "__main__":
    main()
