"""Run the default edge caching and resource allocation simulation."""

from config import SimulationConfig
from src.simulation import run_strategy_comparison
from src.visualization import ensure_results_dirs, plot_metric_bar


def main() -> None:
    """Run the default scenario, save metrics, and generate summary figures."""

    config = SimulationConfig()
    results = run_strategy_comparison(config)

    data_dir, figure_dir = ensure_results_dirs(config.results_dir)
    results.to_csv(data_dir / "main_summary.csv", index=False)

    plot_metric_bar(
        results,
        metric="avg_latency_ms",
        ylabel="Average Latency (ms)",
        output_path=figure_dir / "main_average_latency.png",
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

    print("\nDefault simulation results:")
    print(results.round(3).to_string(index=False))
    print(f"\nSaved CSV results to: {data_dir}")
    print(f"Saved figures to: {figure_dir}")


if __name__ == "__main__":
    main()
