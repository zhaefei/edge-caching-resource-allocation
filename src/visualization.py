"""Plotting utilities for simulation results."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def ensure_results_dirs(results_dir: Path) -> tuple[Path, Path]:
    """Create data and figure output folders if they do not exist."""

    data_dir = results_dir / "data"
    figure_dir = results_dir / "figures"
    data_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    return data_dir, figure_dir


def plot_metric_bar(
    results: pd.DataFrame,
    metric: str,
    ylabel: str,
    output_path: Path,
) -> None:
    """Create a bar chart for one metric across strategies."""

    plt.figure(figsize=(10, 5))
    plt.bar(results["strategy"], results[metric], color="#4c78a8")
    plt.ylabel(ylabel)
    plt.xticks(rotation=20, ha="right")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_experiment_line(
    results: pd.DataFrame,
    x_column: str,
    y_column: str,
    ylabel: str,
    title: str,
    output_path: Path,
) -> None:
    """Create a line plot for an experiment sweep."""

    plt.figure(figsize=(9, 5))

    for strategy, group in results.groupby("strategy"):
        group = group.sort_values(x_column)
        plt.plot(
            group[x_column],
            group[y_column],
            marker="o",
            linewidth=2,
            label=strategy,
        )

    plt.xlabel(x_column.replace("_", " ").title())
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
