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
                _format_float(float(row["bandwidth_fairness_index"]), 3),
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
            "Bandwidth fairness",
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


def _held_out_mab_table(mab_results: pd.DataFrame) -> str:
    """Format the single-seed held-out caching comparison."""

    rows = []
    for _, row in mab_results.iterrows():
        rows.append(
            [
                str(row["strategy"]),
                _format_float(float(row["avg_latency_ms"]), 2),
                _format_float(float(row["p95_latency_ms"]), 2),
                _format_float(float(row["cache_hit_ratio"]), 3),
                _format_float(float(row["backhaul_load_ratio"]), 3),
            ]
        )
    return _markdown_table(
        [
            "Caching strategy",
            "Avg. latency (ms)",
            "P95 latency (ms)",
            "Cache hit ratio",
            "Backhaul load ratio",
        ],
        rows,
    )


def _multi_seed_v2_table(multi_seed_v2: pd.DataFrame) -> str:
    """Format five-seed strategy means, variation, and paired differences."""

    rows = []
    for _, row in multi_seed_v2.iterrows():
        rows.append(
            [
                str(row["strategy"]),
                (
                    f"{_format_float(float(row['avg_latency_ms_mean']), 2)} "
                    f"+/- {_format_float(float(row['avg_latency_ms_std']), 2)}"
                ),
                (
                    f"{_format_float(float(row['cache_hit_ratio_mean']), 3)} "
                    f"+/- {_format_float(float(row['cache_hit_ratio_std']), 3)}"
                ),
                (
                    f"{float(row['avg_latency_ms_delta_vs_random_mean']):+.2f} "
                    f"+/- {_format_float(float(row['avg_latency_ms_delta_vs_random_std']), 2)}"
                ),
            ]
        )
    return _markdown_table(
        [
            "Caching strategy",
            "Avg. latency mean +/- std (ms)",
            "Hit ratio mean +/- std",
            "Paired latency difference vs random (ms)",
        ],
        rows,
    )


def _mab_diagnostics_table(
    single_seed_diagnostics: pd.Series,
    multi_seed_diagnostics: pd.Series,
) -> str:
    """Format MAB exploration and cache-utilization diagnostics."""

    utilization_mean = _format_float(
        float(multi_seed_diagnostics["mean_final_cache_utilization_mean"]),
        3,
    )
    utilization_std = _format_float(
        float(multi_seed_diagnostics["mean_final_cache_utilization_std"]),
        3,
    )
    rows = [
        [
            "Seed 42",
            str(int(single_seed_diagnostics["completed_epochs"])),
            _format_float(
                float(single_seed_diagnostics["explored_arm_fraction"]),
                3,
            ),
            _format_float(
                float(single_seed_diagnostics["mean_final_cache_utilization"]),
                3,
            ),
        ],
        [
            "Five-seed mean +/- std",
            (
                f"{_format_float(float(multi_seed_diagnostics['completed_epochs_mean']), 2)} "
                f"+/- {_format_float(float(multi_seed_diagnostics['completed_epochs_std']), 2)}"
            ),
            (
                f"{_format_float(float(multi_seed_diagnostics['explored_arm_fraction_mean']), 3)} "
                "+/- "
                f"{_format_float(float(multi_seed_diagnostics['explored_arm_fraction_std']), 3)}"
            ),
            (
                f"{utilization_mean} +/- {utilization_std}"
            ),
        ],
    ]
    return _markdown_table(
        [
            "Scope",
            "Completed epochs",
            "Explored-arm fraction",
            "Mean cache utilization",
        ],
        rows,
    )


def main() -> None:
    config = SimulationConfig()
    data_dir = config.results_dir / "data"
    report_dir = Path("report")
    main_summary_path = data_dir / "main_summary.csv"
    multi_seed_path = data_dir / "multi_seed_cache_capacity_summary.csv"
    mab_comparison_path = data_dir / "mab_comparison_experiment.csv"
    mab_diagnostics_path = data_dir / "mab_comparison_diagnostics.csv"
    multi_seed_v2_path = data_dir / "multi_seed_v2_summary.csv"
    multi_seed_v2_diagnostics_path = (
        data_dir / "multi_seed_v2_mab_diagnostics_summary.csv"
    )
    spatial_locality_path = data_dir / "spatial_locality_experiment.csv"
    user_activity_path = data_dir / "user_activity_experiment.csv"

    if not main_summary_path.exists():
        raise FileNotFoundError(
            "Missing results/data/main_summary.csv. Run `python main.py` first."
        )
    if not multi_seed_path.exists():
        raise FileNotFoundError(
            "Missing multi-seed summary. Run `python run_all_experiments.py` first."
        )
    if not spatial_locality_path.exists():
        raise FileNotFoundError(
            "Missing spatial locality experiment. Run `python run_all_experiments.py` first."
        )
    if not user_activity_path.exists():
        raise FileNotFoundError(
            "Missing user activity experiment. Run `python run_all_experiments.py` first."
        )
    for required_path in (
        mab_comparison_path,
        mab_diagnostics_path,
        multi_seed_v2_path,
        multi_seed_v2_diagnostics_path,
    ):
        if not required_path.exists():
            raise FileNotFoundError(
                f"Missing {required_path.name}. Run `python run_all_experiments.py` first."
            )

    main_results = pd.read_csv(main_summary_path)
    multi_seed_results = pd.read_csv(multi_seed_path)
    mab_comparison_results = pd.read_csv(mab_comparison_path)
    mab_diagnostics = pd.read_csv(mab_diagnostics_path).iloc[0]
    multi_seed_v2_results = pd.read_csv(multi_seed_v2_path)
    multi_seed_v2_diagnostics = pd.read_csv(
        multi_seed_v2_diagnostics_path
    ).iloc[0]
    mab_v2_row = multi_seed_v2_results.loc[
        multi_seed_v2_results["strategy"] == "UCB-style MAB caching + equal BW"
    ].iloc[0]
    spatial_locality_results = pd.read_csv(spatial_locality_path)
    user_activity_results = pd.read_csv(user_activity_path)
    locality_local = spatial_locality_results[
        spatial_locality_results["strategy"] == "Local popularity caching + equal BW"
    ]
    locality_global = spatial_locality_results[
        spatial_locality_results["strategy"] == "Popularity caching + equal BW"
    ]
    locality_comparison = locality_local.merge(
        locality_global,
        on="spatial_locality_strength",
        suffixes=("_local", "_global"),
    )
    strongest_locality = locality_comparison.sort_values(
        "spatial_locality_strength"
    ).iloc[-1]
    activity_equal = user_activity_results[
        user_activity_results["strategy"] == "Greedy caching + equal BW"
    ]
    activity_demand = user_activity_results[
        user_activity_results["strategy"] == "Greedy caching + demand-aware BW"
    ]
    activity_comparison = activity_equal.merge(
        activity_demand,
        on="user_activity_alpha",
        suffixes=("_equal", "_demand"),
    )
    strongest_activity_skew = activity_comparison.sort_values(
        "user_activity_alpha"
    ).iloc[-1]

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
        "## Cache-Capacity Multi-Seed Results at Default Budget",
        "",
        _multi_seed_table(multi_seed_results, config.cache_capacity),
        "",
        "## Held-Out MAB Comparison (Seed 42)",
        "",
        _held_out_mab_table(mab_comparison_results),
        "",
        "## Five-Seed V2 Strategy Summary",
        "",
        _multi_seed_v2_table(multi_seed_v2_results),
        "",
        "Negative paired latency differences indicate lower latency than the",
        "same-seed random caching baseline.",
        "",
        "## MAB Learning Diagnostics",
        "",
        _mab_diagnostics_table(mab_diagnostics, multi_seed_v2_diagnostics),
        "",
        "## Figure References",
        "",
        "- Network topology: `docs/figures/network_topology.png`",
        "- Zipf content popularity: `docs/figures/content_popularity_zipf.png`",
        "- Latency vs cache capacity: `docs/figures/latency_vs_cache_capacity.png`",
        "- Multi-seed latency trend: `docs/figures/multi_seed_latency_vs_cache_capacity.png`",
        "- Spatial locality sensitivity: `docs/figures/latency_vs_spatial_locality.png`",
        "- User activity skew sensitivity: `docs/figures/latency_vs_user_activity.png`",
        "- User activity fairness sensitivity: `docs/figures/fairness_vs_user_activity.png`",
        "- Backhaul sensitivity: `docs/figures/latency_vs_backhaul_latency.png`",
        "- Bandwidth sensitivity: `docs/figures/latency_vs_bandwidth.png`",
        "- File-size variability sensitivity: `docs/figures/latency_vs_file_size_variability.png`",
        "- P95 latency by strategy: `docs/figures/main_p95_latency.png`",
        "- Bandwidth fairness by strategy: `docs/figures/main_bandwidth_fairness.png`",
        "- Latency component breakdown: `docs/figures/main_latency_breakdown.png`",
        "- Final v2 latency mean/std: `docs/figures/v2_strategy_latency_mean_std.png`",
        "- Final v2 hit-ratio mean/std: `docs/figures/v2_strategy_hit_ratio_mean_std.png`",
        "- Final paired latency difference: `docs/figures/v2_paired_latency_vs_random.png`",
        "",
        "## Spatial Locality Discussion Sentence",
        "",
        (
            "When server-specific demand becomes stronger, local popularity caching "
            "benefits more from using nearby request traces instead of one global "
            "ranking. At the strongest tested locality setting "
            f"({strongest_locality['spatial_locality_strength']:.1f}), local "
            "popularity caching lowers average latency from "
            f"{_format_float(float(strongest_locality['avg_latency_ms_global']), 2)} ms "
            "to "
            f"{_format_float(float(strongest_locality['avg_latency_ms_local']), 2)} ms."
        ),
        "",
        "## User Activity Skew Discussion Sentence",
        "",
        (
            "When user demand becomes more uneven, demand-aware bandwidth "
            "allocation becomes easier to justify because a small set of active "
            "users account for a larger fraction of requests. At the strongest "
            f"tested activity skew ({strongest_activity_skew['user_activity_alpha']:.1f}), "
            "greedy caching with demand-aware bandwidth lowers average latency "
            "from "
            f"{_format_float(float(strongest_activity_skew['avg_latency_ms_equal']), 2)} ms "
            "under equal bandwidth to "
            f"{_format_float(float(strongest_activity_skew['avg_latency_ms_demand']), 2)} ms, "
            "with bandwidth fairness changing from "
            f"{_format_float(float(strongest_activity_skew['bandwidth_fairness_index_equal']), 3)} "
            "to "
            f"{_format_float(float(strongest_activity_skew['bandwidth_fairness_index_demand']), 3)}."
        ),
        "",
        "## Suggested Discussion Sentence",
        "",
        (
            "In the default simulation, caching-aware strategies improve cache hit "
            "ratio and reduce backhaul load compared with random caching. The "
            "demand-aware bandwidth allocation variant achieves the lowest average "
            "latency in the default scenario, while the reported 95th percentile "
            "latency and Jain's bandwidth fairness index help check whether this "
            "average gain also improves tail performance and preserves a balanced "
            "resource distribution. The multi-seed experiment shows that the same "
            "trend remains visible across random network realizations."
        ),
        "",
        "## V2 Learning-Based Discussion Sentence",
        "",
        (
            "Across five fixed seeds, UCB-style MAB caching records "
            f"{_format_float(float(mab_v2_row['avg_latency_ms_mean']), 2)} "
            "ms mean latency and changes latency by "
            f"{float(mab_v2_row['avg_latency_ms_delta_vs_random_mean']):+.2f} "
            "ms relative to the same-seed random baseline. However, it does not "
            "have the lowest mean latency among the informed caching policies, "
            "so the result supports MAB as an understandable adaptive baseline "
            "rather than as a universally superior algorithm."
        ),
        "",
    ]

    output_path = report_dir / "generated_results.md"
    output_path.write_text("\n".join(content), encoding="utf-8")
    print(f"Generated report assets: {output_path}")


if __name__ == "__main__":
    main()
