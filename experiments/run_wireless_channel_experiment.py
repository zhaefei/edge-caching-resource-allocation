"""Compare path-loss sensitivity with and without snapshot fading."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import SimulationConfig
from src.reproducibility import write_run_metadata
from src.simulation import run_strategy_comparison
from src.visualization import ensure_results_dirs, plot_experiment_line


DEFAULT_PATH_LOSS_EXPONENTS = (2.6, 3.0, 3.4, 3.8, 4.2)
DEFAULT_CHANNEL_MODELS = ("path_loss", "path_loss_fading")
CHANNEL_MODEL_LABELS = {
    "path_loss": "Path loss",
    "path_loss_fading": "Path loss + fading",
}
FOCAL_STRATEGY = "Greedy caching + demand-aware BW"


def run_wireless_channel_experiment(
    base_config: SimulationConfig,
    path_loss_exponents: Sequence[float] = DEFAULT_PATH_LOSS_EXPONENTS,
    channel_models: Sequence[str] = DEFAULT_CHANNEL_MODELS,
) -> pd.DataFrame:
    """Run controlled channel scenarios and return all strategy metrics."""

    if not path_loss_exponents:
        raise ValueError("At least one path-loss exponent is required.")
    if not channel_models:
        raise ValueError("At least one wireless channel model is required.")

    frames = []
    for channel_model in channel_models:
        if channel_model not in CHANNEL_MODEL_LABELS:
            raise ValueError(f"Unsupported experiment channel model: {channel_model}")

        for exponent in path_loss_exponents:
            config = replace(
                base_config,
                wireless_channel_model=channel_model,
                path_loss_exponent=float(exponent),
            )
            results = run_strategy_comparison(config)
            results["wireless_channel_model"] = channel_model
            results["path_loss_exponent"] = float(exponent)
            frames.append(results)

    return pd.concat(frames, ignore_index=True)


def prepare_focal_channel_results(
    results: pd.DataFrame,
    focal_strategy: str = FOCAL_STRATEGY,
) -> pd.DataFrame:
    """Select one caching policy and label channel models for clear plots."""

    focal_results = results.loc[results["strategy"] == focal_strategy].copy()
    if focal_results.empty:
        raise ValueError(f"Focal strategy not found: {focal_strategy}")

    focal_results["strategy"] = focal_results["wireless_channel_model"].map(
        CHANNEL_MODEL_LABELS
    )
    if focal_results["strategy"].isna().any():
        raise ValueError("One or more channel models do not have plot labels.")
    return focal_results


def main() -> None:
    base_config = SimulationConfig()
    all_results = run_wireless_channel_experiment(base_config)
    focal_results = prepare_focal_channel_results(all_results)

    data_dir, figure_dir = ensure_results_dirs(base_config.results_dir)
    data_path = data_dir / "wireless_channel_experiment.csv"
    all_results.to_csv(data_path, index=False)
    write_run_metadata(
        base_config,
        data_dir / "wireless_channel_experiment_metadata.json",
        run_name="wireless_channel_experiment",
        extra_metadata={
            "sweep_parameter": "path_loss_exponent_and_channel_model",
            "sweep_values": {
                "path_loss_exponent": list(DEFAULT_PATH_LOSS_EXPONENTS),
                "wireless_channel_model": list(DEFAULT_CHANNEL_MODELS),
            },
            "focal_strategy_for_figures": FOCAL_STRATEGY,
            "output_files": [
                "results/data/wireless_channel_experiment.csv",
                "results/figures/latency_vs_path_loss_exponent.png",
                "results/figures/rate_vs_path_loss_exponent.png",
            ],
        },
    )

    plot_experiment_line(
        focal_results,
        x_column="path_loss_exponent",
        y_column="avg_latency_ms",
        ylabel="Average Latency (ms)",
        title="Channel Sensitivity: Latency vs Path-Loss Exponent",
        output_path=figure_dir / "latency_vs_path_loss_exponent.png",
        xlabel="Path-Loss Exponent",
    )
    plot_experiment_line(
        focal_results,
        x_column="path_loss_exponent",
        y_column="avg_wireless_rate_mbps",
        ylabel="Average Wireless Rate (Mbps)",
        title="Channel Sensitivity: Rate vs Path-Loss Exponent",
        output_path=figure_dir / "rate_vs_path_loss_exponent.png",
        xlabel="Path-Loss Exponent",
    )

    print("Wireless channel sensitivity experiment completed.")
    print(f"Saved data to {data_path}")


if __name__ == "__main__":
    main()
