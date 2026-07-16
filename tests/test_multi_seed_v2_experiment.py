"""Tests for the final-strategy multi-seed v2 experiment."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from config import SimulationConfig
from experiments.run_multi_seed_v2_experiment import (
    run_multi_seed_v2_experiment,
)
from src.simulation import MAB_COMPARISON_STRATEGIES


class MultiSeedV2ExperimentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = SimulationConfig(
            seed=9,
            num_files=10,
            num_users=18,
            num_edge_servers=3,
            cache_capacity=3,
            num_requests=300,
            mab_training_fraction=0.60,
            mab_update_interval=20,
        )
        self.seeds = (3, 7, 11)

    def test_multi_seed_results_are_reproducible_and_structured(self) -> None:
        first = run_multi_seed_v2_experiment(self.config, self.seeds)
        second = run_multi_seed_v2_experiment(self.config, self.seeds)

        pd.testing.assert_frame_equal(first.raw_metrics, second.raw_metrics)
        pd.testing.assert_frame_equal(first.summary_metrics, second.summary_metrics)
        pd.testing.assert_frame_equal(
            first.raw_mab_diagnostics,
            second.raw_mab_diagnostics,
        )
        pd.testing.assert_frame_equal(
            first.summary_mab_diagnostics,
            second.summary_mab_diagnostics,
        )

        self.assertEqual(
            len(first.raw_metrics),
            len(self.seeds) * len(MAB_COMPARISON_STRATEGIES),
        )
        self.assertEqual(len(first.summary_metrics), len(MAB_COMPARISON_STRATEGIES))
        self.assertEqual(len(first.raw_mab_diagnostics), len(self.seeds))
        self.assertEqual(len(first.summary_mab_diagnostics), 1)
        self.assertEqual(set(first.raw_metrics["seed"]), set(self.seeds))
        self.assertEqual(
            list(first.summary_metrics["strategy"]),
            list(MAB_COMPARISON_STRATEGIES),
        )
        self.assertTrue(
            (first.summary_metrics["seed_count"] == len(self.seeds)).all()
        )
        self.assertTrue(
            (first.raw_metrics["actual_training_fraction"] == 0.60).all()
        )
        random_rows = first.raw_metrics.loc[
            first.raw_metrics["strategy"] == MAB_COMPARISON_STRATEGIES[0]
        ]
        paired_columns = [
            column
            for column in first.raw_metrics.columns
            if column.endswith("_delta_vs_random")
        ]
        self.assertEqual(len(paired_columns), 4)
        self.assertTrue((random_rows[paired_columns] == 0.0).all().all())
        self.assertTrue(np.isfinite(first.raw_metrics[paired_columns]).all().all())

        for _, seed_results in first.raw_metrics.groupby("seed"):
            self.assertEqual(len(seed_results), len(MAB_COMPARISON_STRATEGIES))
            self.assertEqual(seed_results["avg_wireless_rate_mbps"].nunique(), 1)
            self.assertEqual(seed_results["bandwidth_fairness_index"].nunique(), 1)

        mean_columns = [
            column
            for column in first.summary_metrics.columns
            if column.endswith("_mean")
        ]
        std_columns = [
            column
            for column in first.summary_metrics.columns
            if column.endswith("_std")
        ]
        self.assertTrue(np.isfinite(first.summary_metrics[mean_columns]).all().all())
        self.assertTrue(np.isfinite(first.summary_metrics[std_columns]).all().all())
        self.assertTrue((first.summary_metrics[std_columns] >= 0.0).all().all())

    def test_summary_matches_raw_mab_rows_and_diagnostics(self) -> None:
        result = run_multi_seed_v2_experiment(self.config, self.seeds)
        mab_raw = result.raw_metrics.loc[
            result.raw_metrics["strategy"] == MAB_COMPARISON_STRATEGIES[-1]
        ]
        mab_summary = result.summary_metrics.loc[
            result.summary_metrics["strategy"] == MAB_COMPARISON_STRATEGIES[-1]
        ].iloc[0]

        self.assertAlmostEqual(
            float(mab_summary["avg_latency_ms_mean"]),
            float(mab_raw["avg_latency_ms"].mean()),
        )
        self.assertAlmostEqual(
            float(mab_summary["avg_latency_ms_std"]),
            float(mab_raw["avg_latency_ms"].std(ddof=1)),
        )
        self.assertAlmostEqual(
            float(mab_summary["cache_hit_ratio_mean"]),
            float(mab_raw["cache_hit_ratio"].mean()),
        )
        self.assertAlmostEqual(
            float(mab_summary["cache_hit_ratio_std"]),
            float(mab_raw["cache_hit_ratio"].std(ddof=1)),
        )
        self.assertAlmostEqual(
            float(mab_summary["avg_latency_ms_delta_vs_random_mean"]),
            float(mab_raw["avg_latency_ms_delta_vs_random"].mean()),
        )
        self.assertAlmostEqual(
            float(mab_summary["avg_latency_ms_delta_vs_random_std"]),
            float(mab_raw["avg_latency_ms_delta_vs_random"].std(ddof=1)),
        )

        diagnostic_summary = result.summary_mab_diagnostics.iloc[0]
        self.assertEqual(int(diagnostic_summary["seed_count"]), len(self.seeds))
        self.assertAlmostEqual(
            float(diagnostic_summary["explored_arm_fraction_mean"]),
            float(result.raw_mab_diagnostics["explored_arm_fraction"].mean()),
        )
        self.assertAlmostEqual(
            float(diagnostic_summary["explored_arm_fraction_std"]),
            float(
                result.raw_mab_diagnostics["explored_arm_fraction"].std(ddof=1)
            ),
        )
        self.assertTrue(
            result.raw_mab_diagnostics["explored_arm_fraction"]
            .between(0.0, 1.0)
            .all()
        )
        self.assertTrue(
            result.raw_mab_diagnostics["mean_final_cache_utilization"]
            .between(0.0, 1.0 + 1e-9)
            .all()
        )

    def test_seed_list_validation_rejects_unusable_inputs(self) -> None:
        invalid_seed_sets = (
            (),
            (1,),
            (1, 1),
            (1, -2),
            (1, 2.5),
            (True, 2),
        )

        for seeds in invalid_seed_sets:
            with self.subTest(seeds=seeds):
                with self.assertRaises(ValueError):
                    run_multi_seed_v2_experiment(self.config, seeds)


if __name__ == "__main__":
    unittest.main()
