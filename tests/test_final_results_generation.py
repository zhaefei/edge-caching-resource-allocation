"""Tests for final v2 figures and source-backed findings generation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from config import SimulationConfig
from generate_final_figures import (
    FINAL_STRATEGY_LABELS,
    generate_final_v2_figures,
    prepare_final_figure_data,
)
from src.simulation import MAB_COMPARISON_STRATEGIES
from summarize_results import build_key_findings


class FinalResultsGenerationTests(unittest.TestCase):
    def test_final_figure_data_is_validated_and_ordered(self) -> None:
        summary = _sample_v2_summary()

        prepared = prepare_final_figure_data(summary.sample(frac=1.0, random_state=3))

        self.assertEqual(
            list(prepared["strategy"]),
            list(MAB_COMPARISON_STRATEGIES),
        )
        self.assertEqual(
            list(prepared["plot_label"]),
            [FINAL_STRATEGY_LABELS[name] for name in MAB_COMPARISON_STRATEGIES],
        )

        missing_strategy = summary.iloc[:-1].copy()
        with self.assertRaisesRegex(ValueError, "final strategy set"):
            prepare_final_figure_data(missing_strategy)

        invalid_std = summary.copy()
        invalid_std.loc[0, "avg_latency_ms_std"] = -1.0
        with self.assertRaisesRegex(ValueError, "non-negative"):
            prepare_final_figure_data(invalid_std)

    def test_final_figures_are_nonempty_and_mirrored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            result_paths = generate_final_v2_figures(
                _sample_v2_summary(),
                root / "results",
                root / "docs",
            )

            self.assertEqual(len(result_paths), 6)
            for path in result_paths:
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 1000)

            for result_path, docs_path in zip(result_paths[:3], result_paths[3:]):
                self.assertEqual(result_path.name, docs_path.name)
                self.assertEqual(result_path.read_bytes(), docs_path.read_bytes())

    def test_key_findings_use_generated_values_and_state_limits(self) -> None:
        config = replace(SimulationConfig(), results_dir=Path("unused"))
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            _write_findings_inputs(data_dir)

            content = build_key_findings(config, data_dir)

        self.assertIn("## Default Scenario", content)
        self.assertIn("reduces average latency by 20.0%", content)
        self.assertIn("## Held-Out MAB Comparison (Seed 42)", content)
        self.assertIn("85.000 ms average latency", content)
        self.assertIn("not the lowest-latency policy", content)
        self.assertIn("## Five-Seed V2 Summary", content)
        self.assertIn("82.000 +/- 3.000 ms", content)
        self.assertIn("-18.000 +/- 2.000 ms", content)
        self.assertIn("## Interpretation Boundary", content)
        self.assertIn("not a novel or guaranteed-optimal", content)


def _sample_v2_summary() -> pd.DataFrame:
    rows = []
    for index, strategy in enumerate(MAB_COMPARISON_STRATEGIES):
        rows.append(
            {
                "strategy": strategy,
                "seed_count": 5,
                "avg_latency_ms_mean": 100.0 - 5.0 * index,
                "avg_latency_ms_std": 3.0 + index,
                "cache_hit_ratio_mean": 0.20 + 0.08 * index,
                "cache_hit_ratio_std": 0.02,
                "avg_latency_ms_delta_vs_random_mean": -5.0 * index,
                "avg_latency_ms_delta_vs_random_std": 0.0 if index == 0 else 1.5,
            }
        )
    return pd.DataFrame(rows)


def _write_findings_inputs(data_dir: Path) -> None:
    default_rows = [
        _default_metric_row("Random caching + equal BW", 100.0, 0.10, 100.0, 5.0, 1.0),
        _default_metric_row(
            "Local popularity caching + equal BW",
            90.0,
            0.45,
            55.0,
            5.0,
            1.0,
        ),
        _default_metric_row(
            "Greedy caching + equal BW",
            82.0,
            0.50,
            42.0,
            5.0,
            1.0,
        ),
        _default_metric_row(
            "Greedy caching + demand-aware BW",
            80.0,
            0.50,
            40.0,
            6.0,
            0.8,
        ),
    ]
    pd.DataFrame(default_rows).to_csv(data_dir / "main_summary.csv", index=False)

    pd.DataFrame(
        [
            {
                "strategy": "Random caching + equal BW",
                "avg_latency_ms": 100.0,
                "cache_hit_ratio": 0.10,
            },
            {
                "strategy": "Greedy caching + equal BW",
                "avg_latency_ms": 80.0,
                "cache_hit_ratio": 0.50,
            },
            {
                "strategy": "UCB-style MAB caching + equal BW",
                "avg_latency_ms": 85.0,
                "cache_hit_ratio": 0.45,
            },
        ]
    ).to_csv(data_dir / "mab_comparison_experiment.csv", index=False)
    pd.DataFrame(
        [
            {
                "completed_epochs": 10,
                "explored_arm_fraction": 0.9,
                "mean_final_cache_utilization": 0.95,
            }
        ]
    ).to_csv(data_dir / "mab_comparison_diagnostics.csv", index=False)

    pd.DataFrame(
        [
            {
                "strategy": "Prior-informed popularity caching + equal BW",
                "avg_latency_ms_mean": 79.0,
                "avg_latency_ms_std": 2.5,
                "avg_latency_ms_delta_vs_random_mean": -21.0,
                "avg_latency_ms_delta_vs_random_std": 1.5,
                "cache_hit_ratio_delta_vs_random_mean": 0.32,
                "cache_hit_ratio_delta_vs_random_std": 0.01,
            },
            {
                "strategy": "UCB-style MAB caching + equal BW",
                "avg_latency_ms_mean": 82.0,
                "avg_latency_ms_std": 3.0,
                "avg_latency_ms_delta_vs_random_mean": -18.0,
                "avg_latency_ms_delta_vs_random_std": 2.0,
                "cache_hit_ratio_delta_vs_random_mean": 0.30,
                "cache_hit_ratio_delta_vs_random_std": 0.02,
            },
        ]
    ).to_csv(data_dir / "multi_seed_v2_summary.csv", index=False)
    pd.DataFrame(
        [
            {
                "explored_arm_fraction_mean": 0.92,
                "mean_final_cache_utilization_mean": 0.96,
            }
        ]
    ).to_csv(
        data_dir / "multi_seed_v2_mab_diagnostics_summary.csv",
        index=False,
    )


def _default_metric_row(
    strategy: str,
    latency_ms: float,
    hit_ratio: float,
    backhaul_traffic_mbits: float,
    wireless_rate_mbps: float,
    fairness: float,
) -> dict[str, str | float]:
    return {
        "strategy": strategy,
        "avg_latency_ms": latency_ms,
        "cache_hit_ratio": hit_ratio,
        "backhaul_traffic_mbits": backhaul_traffic_mbits,
        "avg_wireless_rate_mbps": wireless_rate_mbps,
        "bandwidth_fairness_index": fairness,
    }


if __name__ == "__main__":
    unittest.main()
