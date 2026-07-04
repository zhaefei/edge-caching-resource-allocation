"""Run the default edge caching and resource allocation simulation."""

import numpy as np

from config import SimulationConfig
from src.network import generate_network
from src.request_model import generate_request_trace
from src.reproducibility import write_run_metadata
from src.simulation import run_strategy_comparison
from src.visualization import (
    ensure_results_dirs,
    plot_content_popularity,
    plot_metric_bar,
    plot_network_topology,
)


def main() -> None:
    """Run the default scenario, save metrics, and generate summary figures."""

    config = SimulationConfig()
    results = run_strategy_comparison(config)

    data_dir, figure_dir = ensure_results_dirs(config.results_dir)
    results.to_csv(data_dir / "main_summary.csv", index=False)
    write_run_metadata(
        config,
        data_dir / "default_run_metadata.json",
        run_name="default_simulation",
    )

    rng = np.random.default_rng(config.seed)
    network = generate_network(config, rng)
    trace = generate_request_trace(config, rng, network)

    plot_network_topology(
        network,
        area_size_m=config.area_size_m,
        output_path=figure_dir / "network_topology.png",
    )
    plot_content_popularity(
        trace.popularity,
        output_path=figure_dir / "content_popularity_zipf.png",
    )
    plot_metric_bar(
        results,
        metric="avg_latency_ms",
        ylabel="Average Latency (ms)",
        output_path=figure_dir / "main_average_latency.png",
    )
    plot_metric_bar(
        results,
        metric="p95_latency_ms",
        ylabel="95th Percentile Latency (ms)",
        output_path=figure_dir / "main_p95_latency.png",
    )
    plot_metric_bar(
        results,
        metric="cache_hit_ratio",
        ylabel="Cache Hit Ratio",
        output_path=figure_dir / "main_cache_hit_ratio.png",
    )
    plot_metric_bar(
        results,
        metric="backhaul_traffic_mbits",
        ylabel="Backhaul Traffic (Mbits)",
        output_path=figure_dir / "main_backhaul_traffic.png",
    )
    plot_metric_bar(
        results,
        metric="avg_wireless_rate_mbps",
        ylabel="Average Wireless Rate (Mbps)",
        output_path=figure_dir / "main_wireless_rate.png",
    )
    plot_metric_bar(
        results,
        metric="bandwidth_fairness_index",
        ylabel="Jain's Bandwidth Fairness Index",
        output_path=figure_dir / "main_bandwidth_fairness.png",
    )

    print("\nDefault simulation results:")
    print(results.round(3).to_string(index=False))
    print(f"\nSaved CSV results to: {data_dir}")
    print(f"Saved figures to: {figure_dir}")


if __name__ == "__main__":
    main()
