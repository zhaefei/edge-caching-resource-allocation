"""Sweep backhaul latency to study when edge caching is most useful."""

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
    backhaul_latencies_ms = [20, 40, 60, 80, 120, 160, 200]
    frames = []

    for latency_ms in backhaul_latencies_ms:
        config = replace(base_config, backhaul_latency_ms=float(latency_ms))
        results = run_strategy_comparison(config)
        results["backhaul_latency_ms"] = latency_ms
        frames.append(results)

    all_results = pd.concat(frames, ignore_index=True)
    data_dir, figure_dir = ensure_results_dirs(base_config.results_dir)
    all_results.to_csv(data_dir / "backhaul_sensitivity_experiment.csv", index=False)
    write_run_metadata(
        base_config,
        data_dir / "backhaul_sensitivity_experiment_metadata.json",
        run_name="backhaul_sensitivity_experiment",
        extra_metadata={
            "sweep_parameter": "backhaul_latency_ms",
            "sweep_values": backhaul_latencies_ms,
            "output_files": [
                "results/data/backhaul_sensitivity_experiment.csv",
                "results/figures/latency_vs_backhaul_latency.png",
                "results/figures/backhaul_delay_vs_backhaul_latency.png",
            ],
        },
    )

    plot_experiment_line(
        all_results,
        x_column="backhaul_latency_ms",
        y_column="avg_latency_ms",
        ylabel="Average Latency (ms)",
        title="Latency vs Backhaul Latency",
        output_path=figure_dir / "latency_vs_backhaul_latency.png",
        xlabel="Backhaul Latency (ms)",
    )
    plot_experiment_line(
        all_results,
        x_column="backhaul_latency_ms",
        y_column="avg_backhaul_delay_ms",
        ylabel="Average Backhaul Delay (ms)",
        title="Backhaul Delay vs Backhaul Latency",
        output_path=figure_dir / "backhaul_delay_vs_backhaul_latency.png",
        xlabel="Backhaul Latency (ms)",
    )

    print("Backhaul sensitivity experiment completed.")
    print(f"Saved data to {data_dir / 'backhaul_sensitivity_experiment.csv'}")


if __name__ == "__main__":
    main()
