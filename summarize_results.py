"""Generate a short Markdown summary of the latest simulation results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import SimulationConfig
from src.visualization import ensure_results_dirs


def _format_pct(value: float) -> str:
    return f"{value:.1f}%"


def main() -> None:
    """Read saved CSV files and write a concise key findings summary."""

    config = SimulationConfig()
    data_dir, _ = ensure_results_dirs(config.results_dir)
    main_summary_path = data_dir / "main_summary.csv"
    multi_seed_summary_path = data_dir / "multi_seed_cache_capacity_summary.csv"

    if not main_summary_path.exists():
        raise FileNotFoundError(
            "results/data/main_summary.csv was not found. Run `python main.py` first."
        )

    main_results = pd.read_csv(main_summary_path)
    random_row = main_results.loc[
        main_results["strategy"] == "Random caching + equal BW"
    ].iloc[0]
    best_row = main_results.loc[
        main_results["strategy"] == "Greedy caching + demand-aware BW"
    ].iloc[0]
    local_row = main_results.loc[
        main_results["strategy"] == "Local popularity caching + equal BW"
    ].iloc[0]

    latency_reduction = (
        (random_row["avg_latency_ms"] - best_row["avg_latency_ms"])
        / random_row["avg_latency_ms"]
        * 100.0
    )
    local_latency_reduction = (
        (random_row["avg_latency_ms"] - local_row["avg_latency_ms"])
        / random_row["avg_latency_ms"]
        * 100.0
    )
    hit_ratio_gain_pp = (
        best_row["cache_hit_ratio"] - random_row["cache_hit_ratio"]
    ) * 100.0
    backhaul_reduction = (
        (
            random_row["backhaul_traffic_mbits"]
            - best_row["backhaul_traffic_mbits"]
        )
        / random_row["backhaul_traffic_mbits"]
        * 100.0
    )
    rate_gain = (
        (best_row["avg_wireless_rate_mbps"] - random_row["avg_wireless_rate_mbps"])
        / random_row["avg_wireless_rate_mbps"]
        * 100.0
    )

    lines = [
        "# Key Findings",
        "",
        "These findings are generated from the default simulation outputs.",
        "",
        (
            "- Compared with random caching, greedy caching with demand-aware "
            f"bandwidth allocation reduces average latency by {_format_pct(latency_reduction)}."
        ),
        (
            "- Local popularity caching reduces average latency by "
            f"{_format_pct(local_latency_reduction)} compared with random caching."
        ),
        (
            "- Cache hit ratio improves by "
            f"{hit_ratio_gain_pp:.1f} percentage points compared with random caching."
        ),
        (
            "- Backhaul traffic decreases by "
            f"{_format_pct(backhaul_reduction)}, showing the benefit of serving "
            "popular content at the edge."
        ),
        (
            "- Demand-aware bandwidth allocation increases the request-weighted "
            f"average wireless rate by {_format_pct(rate_gain)} in this default scenario."
        ),
    ]

    if multi_seed_summary_path.exists():
        multi_seed = pd.read_csv(multi_seed_summary_path)
        capacity_rows = multi_seed[multi_seed["cache_capacity"] == config.cache_capacity]
        if not capacity_rows.empty:
            random_seed_row = capacity_rows.loc[
                capacity_rows["strategy"] == "Random caching + equal BW"
            ].iloc[0]
            best_seed_row = capacity_rows.loc[
                capacity_rows["strategy"] == "Greedy caching + demand-aware BW"
            ].iloc[0]
            multi_seed_reduction = (
                (
                    random_seed_row["avg_latency_ms_mean"]
                    - best_seed_row["avg_latency_ms_mean"]
                )
                / random_seed_row["avg_latency_ms_mean"]
                * 100.0
            )
            lines.extend(
                [
                    "",
                    (
                        f"- In the multi-seed experiment at cache capacity {config.cache_capacity}, "
                        "the same best strategy reduces mean latency by "
                        f"{_format_pct(multi_seed_reduction)} relative to random caching."
                    ),
                ]
            )

    output_path = data_dir / "key_findings.md"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print(f"\nSaved summary to {output_path}")


if __name__ == "__main__":
    main()
