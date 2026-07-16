"""Generate the final v2 portfolio figures from multi-seed CSV results."""

from __future__ import annotations

from pathlib import Path
from shutil import copy2

import numpy as np
import pandas as pd

from config import SimulationConfig
from src.reproducibility import write_run_metadata
from src.simulation import MAB_COMPARISON_STRATEGIES
from src.visualization import ensure_results_dirs, plot_strategy_errorbar


FINAL_STRATEGY_LABELS = {
    MAB_COMPARISON_STRATEGIES[0]: "Random",
    MAB_COMPARISON_STRATEGIES[1]: "Prior-informed popularity",
    MAB_COMPARISON_STRATEGIES[2]: "Local popularity",
    MAB_COMPARISON_STRATEGIES[3]: "Greedy latency-aware",
    MAB_COMPARISON_STRATEGIES[4]: "UCB-style MAB",
}

FINAL_FIGURE_FILENAMES = (
    "v2_strategy_latency_mean_std.png",
    "v2_strategy_hit_ratio_mean_std.png",
    "v2_paired_latency_vs_random.png",
)


def prepare_final_figure_data(summary: pd.DataFrame) -> pd.DataFrame:
    """Validate and order the five-strategy multi-seed summary for plotting."""

    required_columns = {
        "strategy",
        "seed_count",
        "avg_latency_ms_mean",
        "avg_latency_ms_std",
        "cache_hit_ratio_mean",
        "cache_hit_ratio_std",
        "avg_latency_ms_delta_vs_random_mean",
        "avg_latency_ms_delta_vs_random_std",
    }
    missing_columns = required_columns - set(summary.columns)
    if missing_columns:
        raise ValueError(
            "multi-seed v2 summary is missing columns: "
            + ", ".join(sorted(missing_columns))
        )
    if summary["strategy"].duplicated().any():
        raise ValueError("multi-seed v2 summary must contain one row per strategy")
    if set(summary["strategy"]) != set(MAB_COMPARISON_STRATEGIES):
        raise ValueError("multi-seed v2 summary does not match the final strategy set")

    prepared = (
        summary.set_index("strategy")
        .loc[list(MAB_COMPARISON_STRATEGIES)]
        .reset_index()
    )
    numeric_columns = sorted(required_columns - {"strategy"})
    numeric_values = prepared[numeric_columns].apply(
        pd.to_numeric,
        errors="raise",
    )
    if not np.isfinite(numeric_values.to_numpy(float)).all():
        raise ValueError("multi-seed v2 figure values must be finite")
    if (numeric_values["seed_count"] < 2).any():
        raise ValueError("final error bars require at least two seeds")
    std_columns = [column for column in numeric_columns if column.endswith("_std")]
    if (numeric_values[std_columns] < 0.0).any().any():
        raise ValueError("final figure standard deviations must be non-negative")

    prepared[numeric_columns] = numeric_values
    prepared["plot_label"] = prepared["strategy"].map(FINAL_STRATEGY_LABELS)
    return prepared


def generate_final_v2_figures(
    summary: pd.DataFrame,
    results_figure_dir: Path,
    docs_figure_dir: Path,
) -> list[Path]:
    """Write final figures to results and mirror them for GitHub documentation."""

    prepared = prepare_final_figure_data(summary)
    results_figure_dir.mkdir(parents=True, exist_ok=True)
    docs_figure_dir.mkdir(parents=True, exist_ok=True)

    latency_path = results_figure_dir / FINAL_FIGURE_FILENAMES[0]
    plot_strategy_errorbar(
        prepared,
        mean_column="avg_latency_ms_mean",
        std_column="avg_latency_ms_std",
        xlabel="Average latency across seeds (ms)",
        title="Five-Seed Held-Out Latency by Caching Policy",
        output_path=latency_path,
        label_column="plot_label",
    )

    hit_ratio_path = results_figure_dir / FINAL_FIGURE_FILENAMES[1]
    plot_strategy_errorbar(
        prepared,
        mean_column="cache_hit_ratio_mean",
        std_column="cache_hit_ratio_std",
        xlabel="Cache hit ratio across seeds",
        title="Five-Seed Held-Out Cache Hit Ratio by Caching Policy",
        output_path=hit_ratio_path,
        label_column="plot_label",
    )

    paired_results = prepared.loc[
        prepared["strategy"] != MAB_COMPARISON_STRATEGIES[0]
    ]
    paired_path = results_figure_dir / FINAL_FIGURE_FILENAMES[2]
    plot_strategy_errorbar(
        paired_results,
        mean_column="avg_latency_ms_delta_vs_random_mean",
        std_column="avg_latency_ms_delta_vs_random_std",
        xlabel="Latency difference vs random (ms; negative is lower)",
        title="Paired Average-Latency Difference Relative to Random Caching",
        output_path=paired_path,
        label_column="plot_label",
        reference_value=0.0,
    )

    result_paths = [latency_path, hit_ratio_path, paired_path]
    documentation_paths = []
    for result_path in result_paths:
        documentation_path = docs_figure_dir / result_path.name
        copy2(result_path, documentation_path)
        documentation_paths.append(documentation_path)
    return [*result_paths, *documentation_paths]


def main() -> None:
    config = SimulationConfig()
    data_dir, results_figure_dir = ensure_results_dirs(config.results_dir)
    summary_path = data_dir / "multi_seed_v2_summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(
            "Missing multi_seed_v2_summary.csv. Run the multi-seed v2 experiment first."
        )

    summary = pd.read_csv(summary_path)
    generated_paths = generate_final_v2_figures(
        summary,
        results_figure_dir,
        Path("docs/figures"),
    )
    metadata_path = data_dir / "final_v2_figures_metadata.json"
    write_run_metadata(
        config,
        metadata_path,
        run_name="final_v2_figures",
        extra_metadata={
            "source_files": ["results/data/multi_seed_v2_summary.csv"],
            "error_bars": "sample standard deviation across five fixed seeds",
            "paired_reference_strategy": MAB_COMPARISON_STRATEGIES[0],
            "output_files": [str(path).replace("\\", "/") for path in generated_paths],
        },
    )

    print("Final v2 figures generated.")
    for path in generated_paths:
        print(f"Saved figure to {path}")


if __name__ == "__main__":
    main()
