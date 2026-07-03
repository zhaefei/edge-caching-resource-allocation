"""Sweep edge server bandwidth to study wireless resource sensitivity."""

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
    bandwidth_mhz_values = [5, 10, 15, 20, 30, 40, 50]
    frames = []

    for bandwidth_mhz in bandwidth_mhz_values:
        config = replace(base_config, bandwidth_hz=float(bandwidth_mhz) * 1e6)
        results = run_strategy_comparison(config)
        results["bandwidth_mhz"] = bandwidth_mhz
        frames.append(results)

    all_results = pd.concat(frames, ignore_index=True)
    data_dir, figure_dir = ensure_results_dirs(base_config.results_dir)
    all_results.to_csv(data_dir / "bandwidth_sensitivity_experiment.csv", index=False)

    plot_experiment_line(
        all_results,
        x_column="bandwidth_mhz",
        y_column="avg_latency_ms",
        ylabel="Average Latency (ms)",
        title="Latency vs Edge Server Bandwidth",
        output_path=figure_dir / "latency_vs_bandwidth.png",
        xlabel="Bandwidth per Edge Server (MHz)",
    )
    plot_experiment_line(
        all_results,
        x_column="bandwidth_mhz",
        y_column="avg_wireless_rate_mbps",
        ylabel="Average Wireless Rate (Mbps)",
        title="Wireless Rate vs Edge Server Bandwidth",
        output_path=figure_dir / "rate_vs_bandwidth.png",
        xlabel="Bandwidth per Edge Server (MHz)",
    )

    print("Bandwidth sensitivity experiment completed.")
    print(f"Saved data to {data_dir / 'bandwidth_sensitivity_experiment.csv'}")


if __name__ == "__main__":
    main()
