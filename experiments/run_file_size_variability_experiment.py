"""Sweep file-size variability to study storage-aware caching behavior."""

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
    file_size_sigmas = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    frames = []

    for sigma in file_size_sigmas:
        config = replace(base_config, file_size_sigma=float(sigma))
        results = run_strategy_comparison(config)
        results["file_size_sigma"] = sigma
        frames.append(results)

    all_results = pd.concat(frames, ignore_index=True)
    data_dir, figure_dir = ensure_results_dirs(base_config.results_dir)
    all_results.to_csv(data_dir / "file_size_variability_experiment.csv", index=False)
    write_run_metadata(
        base_config,
        data_dir / "file_size_variability_experiment_metadata.json",
        run_name="file_size_variability_experiment",
        extra_metadata={
            "sweep_parameter": "file_size_sigma",
            "sweep_values": file_size_sigmas,
            "output_files": [
                "results/data/file_size_variability_experiment.csv",
                "results/figures/latency_vs_file_size_variability.png",
                "results/figures/backhaul_vs_file_size_variability.png",
            ],
        },
    )

    plot_experiment_line(
        all_results,
        x_column="file_size_sigma",
        y_column="avg_latency_ms",
        ylabel="Average Latency (ms)",
        title="Latency vs File Size Variability",
        output_path=figure_dir / "latency_vs_file_size_variability.png",
        xlabel="Lognormal File Size Sigma",
    )
    plot_experiment_line(
        all_results,
        x_column="file_size_sigma",
        y_column="backhaul_traffic_mbits",
        ylabel="Backhaul Traffic (Mbits)",
        title="Backhaul Traffic vs File Size Variability",
        output_path=figure_dir / "backhaul_vs_file_size_variability.png",
        xlabel="Lognormal File Size Sigma",
    )

    print("File size variability experiment completed.")
    print(f"Saved data to {data_dir / 'file_size_variability_experiment.csv'}")


if __name__ == "__main__":
    main()
