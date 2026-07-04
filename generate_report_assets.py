"""Generate Markdown tables and figure references for the project report."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import SimulationConfig


def _format_float(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, separator_line, *row_lines])


def _default_results_table(main_results: pd.DataFrame) -> str:
    rows = []
    for _, row in main_results.iterrows():
        rows.append(
            [
                str(row["strategy"]),
                _format_float(float(row["avg_latency_ms"]), 2),
                _format_float(float(row["p95_latency_ms"]), 2),
                _format_float(float(row["cache_hit_ratio"]), 3),
                _format_float(float(row["backhaul_load_ratio"]), 3),
                _format_float(float(row["avg_wireless_rate_mbps"]), 2),
            ]
        )

    return _markdown_table(
        [
            "Strategy",
            "Avg. latency (ms)",
            "P95 latency (ms)",
            "Cache hit ratio",
            "Backhaul load ratio",
            "Avg. wireless rate (Mbps)",
        ],
        rows,
    )


def _multi_seed_table(
    multi_seed_results: pd.DataFrame,
    cache_capacity: int,
) -> str:
    capacity_rows = multi_seed_results[
        multi_seed_results["cache_capacity"] == cache_capacity
    ].copy()
    capacity_rows = capacity_rows.sort_values("avg_latency_ms_mean")

    rows = []
    for _, row in capacity_rows.iterrows():
        latency = (
            f"{_format_float(float(row['avg_latency_ms_mean']), 2)} "
            f"+/- {_format_float(float(row['avg_latency_ms_std']), 2)}"
        )
        hit_ratio = (
            f"{_format_float(float(row['cache_hit_ratio_mean']), 3)} "
            f"+/- {_format_float(float(row['cache_hit_ratio_std']), 3)}"
        )
        rows.append(
            [
                str(row["strategy"]),
                latency,
                hit_ratio,
                _format_float(float(row["backhaul_load_ratio_mean"]), 3),
            ]
        )

    return _markdown_table(
        [
            "Strategy",
            "Avg. latency mean +/- std (ms)",
            "Cache hit ratio mean +/- std",
            "Mean backhaul load ratio",
        ],
        rows,
    )


def main() -> None:
    config = SimulationConfig()
    data_dir = config.results_dir / "data"
    report_dir = Path("report")
    main_summary_path = data_dir / "main_summary.csv"
    multi_seed_path = data_dir / "multi_seed_cache_capacity_summary.csv"

    if not main_summary_path.exists():
        raise FileNotFoundError(
            "Missing results/data/main_summary.csv. Run `python main.py` first."
        )
    if not multi_seed_path.exists():
        raise FileNotFoundError(
            "Missing multi-seed summary. Run `python run_all_experiments.py` first."
        )

    main_results = pd.read_csv(main_summary_path)
    multi_seed_results = pd.read_csv(multi_seed_path)

    content = [
        "# Generated Report Assets",
        "",
        "This file is generated from the latest CSV results. It is intended to",
        "help copy tables and figure references into the project report.",
        "",
        "## Default Scenario Results",
        "",
        _default_results_table(main_results),
        "",
        "## Multi-Seed Results at Default Cache Capacity",
        "",
        _multi_seed_table(multi_seed_results, config.cache_capacity),
        "",
        "## Figure References",
        "",
        "- Network topology: `docs/figures/network_topology.png`",
        "- Zipf content popularity: `docs/figures/content_popularity_zipf.png`",
        "- Latency vs cache capacity: `docs/figures/latency_vs_cache_capacity.png`",
        "- Multi-seed latency trend: `docs/figures/multi_seed_latency_vs_cache_capacity.png`",
        "- Backhaul sensitivity: `docs/figures/latency_vs_backhaul_latency.png`",
        "- Bandwidth sensitivity: `docs/figures/latency_vs_bandwidth.png`",
        "- File-size variability sensitivity: `docs/figures/latency_vs_file_size_variability.png`",
        "- P95 latency by strategy: `docs/figures/main_p95_latency.png`",
        "",
        "## Suggested Discussion Sentence",
        "",
        (
            "In the default simulation, caching-aware strategies improve cache hit "
            "ratio and reduce backhaul load compared with random caching. The "
            "demand-aware bandwidth allocation variant achieves the lowest average "
            "latency in the default scenario, while the reported 95th percentile "
            "latency helps check whether this average gain also improves tail "
            "performance. The multi-seed experiment shows that the same trend "
            "remains visible across random network realizations."
        ),
        "",
    ]

    output_path = report_dir / "generated_results.md"
    output_path.write_text("\n".join(content), encoding="utf-8")
    print(f"Generated report assets: {output_path}")


if __name__ == "__main__":
    main()
