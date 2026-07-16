"""Generate a short Markdown summary of the latest simulation results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import SimulationConfig
from src.visualization import ensure_results_dirs


def _format_pct(value: float) -> str:
    return f"{value:.1f}%"


def build_key_findings(config: SimulationConfig, data_dir: Path) -> str:
    """Build a source-backed Markdown summary from generated CSV files."""

    main_summary_path = data_dir / "main_summary.csv"
    multi_seed_summary_path = data_dir / "multi_seed_cache_capacity_summary.csv"
    mab_comparison_path = data_dir / "mab_comparison_experiment.csv"
    mab_diagnostics_path = data_dir / "mab_comparison_diagnostics.csv"
    multi_seed_v2_path = data_dir / "multi_seed_v2_summary.csv"
    multi_seed_v2_diagnostics_path = (
        data_dir / "multi_seed_v2_mab_diagnostics_summary.csv"
    )
    file_size_variability_path = data_dir / "file_size_variability_experiment.csv"
    spatial_locality_path = data_dir / "spatial_locality_experiment.csv"
    user_activity_path = data_dir / "user_activity_experiment.csv"

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
    greedy_equal_row = main_results.loc[
        main_results["strategy"] == "Greedy caching + equal BW"
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
    fairness_change = (
        best_row["bandwidth_fairness_index"]
        - greedy_equal_row["bandwidth_fairness_index"]
    )

    lines = [
        "# Key Findings",
        "",
        "All numerical findings below are generated from repository CSV outputs.",
        "",
        "## Default Scenario",
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
        (
            "- Under the same greedy cache placement, demand-aware bandwidth "
            "allocation changes Jain's bandwidth fairness index from "
            f"{greedy_equal_row['bandwidth_fairness_index']:.3f} to "
            f"{best_row['bandwidth_fairness_index']:.3f} "
            f"({fairness_change:+.3f})."
        ),
    ]

    if mab_comparison_path.exists():
        mab_results = pd.read_csv(mab_comparison_path)
        random_mab_row = mab_results.loc[
            mab_results["strategy"] == "Random caching + equal BW"
        ].iloc[0]
        greedy_mab_row = mab_results.loc[
            mab_results["strategy"] == "Greedy caching + equal BW"
        ].iloc[0]
        mab_row = mab_results.loc[
            mab_results["strategy"] == "UCB-style MAB caching + equal BW"
        ].iloc[0]
        lines.extend(
            [
                "",
                "## Held-Out MAB Comparison (Seed 42)",
                "",
                (
                    "- Under the common 60/40 chronological split and equal "
                    "bandwidth, UCB-style MAB records "
                    f"{mab_row['avg_latency_ms']:.3f} ms average latency and a "
                    f"{mab_row['cache_hit_ratio']:.3f} cache hit ratio."
                ),
                (
                    "- The corresponding random and greedy average latencies are "
                    f"{random_mab_row['avg_latency_ms']:.3f} ms and "
                    f"{greedy_mab_row['avg_latency_ms']:.3f} ms, respectively. "
                    "MAB improves on random caching but is not the lowest-latency "
                    "policy in this single-seed run."
                ),
            ]
        )
        if mab_diagnostics_path.exists():
            diagnostics = pd.read_csv(mab_diagnostics_path).iloc[0]
            lines.append(
                "- MAB completes "
                f"{int(diagnostics['completed_epochs'])} training epochs, explores "
                f"{diagnostics['explored_arm_fraction']:.3f} of cache-feasible arms, "
                "and uses "
                f"{diagnostics['mean_final_cache_utilization'] * 100.0:.2f}% "
                "of cache capacity on average."
            )

    if multi_seed_v2_path.exists():
        multi_seed_v2 = pd.read_csv(multi_seed_v2_path)
        mab_v2_row = multi_seed_v2.loc[
            multi_seed_v2["strategy"] == "UCB-style MAB caching + equal BW"
        ].iloc[0]
        lowest_mean_row = multi_seed_v2.sort_values("avg_latency_ms_mean").iloc[0]
        lines.extend(
            [
                "",
                "## Five-Seed V2 Summary",
                "",
                (
                    "- Across seeds 11, 22, 33, 44, and 55, UCB-style MAB "
                    f"records {mab_v2_row['avg_latency_ms_mean']:.3f} +/- "
                    f"{mab_v2_row['avg_latency_ms_std']:.3f} ms average latency "
                    "(mean +/- sample standard deviation)."
                ),
                (
                    "- Relative to the same-seed random baseline, MAB changes "
                    "average latency by "
                    f"{mab_v2_row['avg_latency_ms_delta_vs_random_mean']:+.3f} "
                    f"+/- {mab_v2_row['avg_latency_ms_delta_vs_random_std']:.3f} "
                    "ms and cache hit ratio by "
                    f"{mab_v2_row['cache_hit_ratio_delta_vs_random_mean']:+.4f} "
                    f"+/- {mab_v2_row['cache_hit_ratio_delta_vs_random_std']:.4f}."
                ),
                (
                    f"- {lowest_mean_row['strategy']} has the lowest mean average "
                    f"latency in this five-seed table at "
                    f"{lowest_mean_row['avg_latency_ms_mean']:.3f} ms; the small "
                    "differences among informed policies should not be presented "
                    "as proof of universal ranking."
                ),
            ]
        )
        if multi_seed_v2_diagnostics_path.exists():
            diagnostics_v2 = pd.read_csv(multi_seed_v2_diagnostics_path).iloc[0]
            lines.append(
                "- Across the five seeds, mean MAB arm coverage is "
                f"{diagnostics_v2['explored_arm_fraction_mean']:.3f}, and mean "
                "final cache utilization is "
                f"{diagnostics_v2['mean_final_cache_utilization_mean'] * 100.0:.2f}%."
            )

    lines.extend(["", "## Sensitivity and Robustness Checks"])

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
                        "- In the multi-seed experiment at the default cache budget "
                        f"equivalent to {config.cache_capacity} average-size files, "
                        f"{best_seed_row['strategy']} reduces mean latency by "
                        f"{_format_pct(multi_seed_reduction)} relative to random caching."
                    ),
                ]
            )

    if file_size_variability_path.exists():
        variability_results = pd.read_csv(file_size_variability_path)
        if not variability_results.empty:
            max_sigma = variability_results["file_size_sigma"].max()
            sigma_rows = variability_results[
                variability_results["file_size_sigma"] == max_sigma
            ]
            best_sigma_row = sigma_rows.sort_values("avg_latency_ms").iloc[0]
            lines.extend(
                [
                    "",
                    (
                        f"- In the file-size variability sweep at sigma {max_sigma:.1f}, "
                        f"{best_sigma_row['strategy']} achieves the lowest average latency."
                    ),
                ]
            )

    if spatial_locality_path.exists():
        locality_results = pd.read_csv(spatial_locality_path)
        local_rows = locality_results[
            locality_results["strategy"] == "Local popularity caching + equal BW"
        ]
        global_rows = locality_results[
            locality_results["strategy"] == "Popularity caching + equal BW"
        ]
        if not local_rows.empty and not global_rows.empty:
            comparison = local_rows.merge(
                global_rows,
                on="spatial_locality_strength",
                suffixes=("_local", "_global"),
            )
            max_strength_row = comparison.sort_values(
                "spatial_locality_strength"
            ).iloc[-1]
            hit_ratio_gain_pp = (
                max_strength_row["cache_hit_ratio_local"]
                - max_strength_row["cache_hit_ratio_global"]
            ) * 100.0
            latency_reduction_pct = (
                (
                    max_strength_row["avg_latency_ms_global"]
                    - max_strength_row["avg_latency_ms_local"]
                )
                / max_strength_row["avg_latency_ms_global"]
                * 100.0
            )
            lines.extend(
                [
                    "",
                    (
                        "- In the spatial-locality sweep at strength "
                        f"{max_strength_row['spatial_locality_strength']:.1f}, "
                        "local popularity caching outperforms global popularity "
                        f"caching by {hit_ratio_gain_pp:.1f} hit-ratio percentage "
                        f"points and {_format_pct(latency_reduction_pct)} lower latency."
                    ),
                ]
            )

    if user_activity_path.exists():
        activity_results = pd.read_csv(user_activity_path)
        greedy_equal = activity_results[
            activity_results["strategy"] == "Greedy caching + equal BW"
        ]
        greedy_demand = activity_results[
            activity_results["strategy"] == "Greedy caching + demand-aware BW"
        ]
        if not greedy_equal.empty and not greedy_demand.empty:
            comparison = greedy_equal.merge(
                greedy_demand,
                on="user_activity_alpha",
                suffixes=("_equal", "_demand"),
            )
            strongest_skew = comparison.sort_values("user_activity_alpha").iloc[-1]
            latency_reduction_pct = (
                (
                    strongest_skew["avg_latency_ms_equal"]
                    - strongest_skew["avg_latency_ms_demand"]
                )
                / strongest_skew["avg_latency_ms_equal"]
                * 100.0
            )
            fairness_change = (
                strongest_skew["bandwidth_fairness_index_demand"]
                - strongest_skew["bandwidth_fairness_index_equal"]
            )
            lines.extend(
                [
                    "",
                    (
                        "- In the user-activity sweep at alpha "
                        f"{strongest_skew['user_activity_alpha']:.1f}, demand-aware "
                        "bandwidth allocation under the same greedy cache placement "
                        f"reduces latency by {_format_pct(latency_reduction_pct)} "
                        "relative to equal bandwidth, while changing Jain's "
                        f"fairness index by {fairness_change:+.3f}."
                    ),
                ]
            )

    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            (
                "- The simulator is an undergraduate-level research model, not a "
                "3GPP-compliant system-level simulator or a production optimizer."
            ),
            (
                "- Five fixed seeds provide a lightweight robustness check. They "
                "do not establish statistical significance across real deployments."
            ),
            (
                "- The UCB-style policy is a teaching-oriented adaptive baseline, "
                "not a novel or guaranteed-optimal caching algorithm."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    """Read saved CSV files and write a concise key findings summary."""

    config = SimulationConfig()
    data_dir, _ = ensure_results_dirs(config.results_dir)
    content = build_key_findings(config, data_dir)
    output_path = data_dir / "key_findings.md"
    output_path.write_text(content, encoding="utf-8")

    print(content.rstrip())
    print(f"\nSaved summary to {output_path}")


if __name__ == "__main__":
    main()
