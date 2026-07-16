"""Plotting utilities for simulation results."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.network import NetworkState


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
    title: str | None = None,
) -> None:
    """Create a bar chart for one metric across strategies."""

    plt.figure(figsize=(10, 5))
    plt.bar(results["strategy"], results[metric], color="#4c78a8")
    plt.ylabel(ylabel)
    if title:
        plt.title(title)
    plt.xticks(rotation=20, ha="right")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_latency_breakdown(
    results: pd.DataFrame,
    output_path: Path,
) -> None:
    """Plot wireless and backhaul components of average request latency."""

    plt.figure(figsize=(10, 5))
    strategy_names = results["strategy"]
    wireless_delay = results["avg_wireless_delay_ms"]
    backhaul_delay = results["avg_backhaul_delay_ms"]

    plt.bar(
        strategy_names,
        wireless_delay,
        label="Wireless transmission delay",
        color="#4c78a8",
    )
    plt.bar(
        strategy_names,
        backhaul_delay,
        bottom=wireless_delay,
        label="Backhaul delay",
        color="#f58518",
    )
    plt.ylabel("Average Latency Component (ms)")
    plt.xticks(rotation=20, ha="right")
    plt.grid(axis="y", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_network_topology(
    network: NetworkState,
    area_size_m: float,
    output_path: Path,
) -> None:
    """Plot user locations, edge server locations, and user associations."""

    plt.figure(figsize=(8, 7))

    for server_id in range(network.server_positions.shape[0]):
        users = network.associations == server_id
        plt.scatter(
            network.user_positions[users, 0],
            network.user_positions[users, 1],
            s=22,
            alpha=0.65,
            label=f"Users served by edge {server_id}",
        )

    plt.scatter(
        network.server_positions[:, 0],
        network.server_positions[:, 1],
        marker="s",
        s=180,
        color="black",
        label="Edge servers",
    )

    for server_id, (x_pos, y_pos) in enumerate(network.server_positions):
        plt.text(
            x_pos + 8,
            y_pos + 8,
            f"Edge {server_id}",
            fontsize=9,
            weight="bold",
        )

    plt.xlim(0, area_size_m)
    plt.ylim(0, area_size_m)
    plt.xlabel("x position (m)")
    plt.ylabel("y position (m)")
    plt.title("Simulated Wireless Edge Network Topology")
    plt.grid(alpha=0.25)
    plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8)
    plt.gca().set_aspect("equal", adjustable="box")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_content_popularity(
    popularity: pd.Series | list[float],
    output_path: Path,
    top_n: int = 30,
) -> None:
    """Plot the most popular files under the Zipf request model."""

    popularity_series = pd.Series(popularity).reset_index(drop=True)
    top_popularity = popularity_series.iloc[:top_n]
    file_ranks = range(1, len(top_popularity) + 1)

    plt.figure(figsize=(9, 5))
    plt.bar(file_ranks, top_popularity, color="#59a14f")
    plt.xlim(0.5, len(top_popularity) + 0.5)
    plt.xlabel("File rank")
    plt.ylabel("Request probability")
    plt.title("Zipf Content Popularity Distribution")
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
    xlabel: str | None = None,
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

    plt.xlabel(xlabel or x_column.replace("_", " ").title())
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_experiment_mean_std(
    results: pd.DataFrame,
    x_column: str,
    mean_column: str,
    std_column: str,
    ylabel: str,
    title: str,
    output_path: Path,
    xlabel: str | None = None,
) -> None:
    """Create a line plot with one standard-deviation error band."""

    plt.figure(figsize=(9, 5))

    for strategy, group in results.groupby("strategy"):
        group = group.sort_values(x_column)
        x_values = group[x_column].to_numpy()
        mean_values = group[mean_column].to_numpy()
        std_values = group[std_column].fillna(0.0).to_numpy()

        line = plt.plot(
            x_values,
            mean_values,
            marker="o",
            linewidth=2,
            label=strategy,
        )[0]
        plt.fill_between(
            x_values,
            mean_values - std_values,
            mean_values + std_values,
            color=line.get_color(),
            alpha=0.15,
        )

    plt.xlabel(xlabel or x_column.replace("_", " ").title())
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_strategy_errorbar(
    results: pd.DataFrame,
    mean_column: str,
    std_column: str,
    xlabel: str,
    title: str,
    output_path: Path,
    label_column: str = "strategy",
    reference_value: float | None = None,
) -> None:
    """Plot strategy means with sample-standard-deviation error bars."""

    means = pd.to_numeric(results[mean_column], errors="raise").to_numpy(float)
    standard_deviations = (
        pd.to_numeric(results[std_column], errors="raise")
        .fillna(0.0)
        .to_numpy(float)
    )
    if not np.all(np.isfinite(means)) or not np.all(
        np.isfinite(standard_deviations)
    ):
        raise ValueError("strategy error-bar values must be finite")
    if np.any(standard_deviations < 0.0):
        raise ValueError("strategy standard deviations must be non-negative")

    labels = results[label_column].astype(str).tolist()
    y_positions = np.arange(len(results))
    figure, axis = plt.subplots(figsize=(9, 5.5))
    axis.errorbar(
        means,
        y_positions,
        xerr=standard_deviations,
        fmt="o",
        markersize=7,
        capsize=4,
        linewidth=1.8,
        color="#4c78a8",
        ecolor="#6b7280",
    )
    if reference_value is not None:
        axis.axvline(reference_value, color="#b42318", linestyle="--", linewidth=1.4)
    axis.set_yticks(y_positions, labels)
    axis.invert_yaxis()
    axis.set_xlabel(xlabel)
    axis.set_title(title)
    axis.grid(axis="x", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=200)
    plt.close(figure)
