"""Tests for the held-out UCB-style MAB caching comparison."""

from __future__ import annotations

from dataclasses import replace
import math
import unittest

import numpy as np
import pandas as pd

from config import SimulationConfig
from experiments.run_mab_comparison_experiment import (
    build_mab_diagnostics_record,
)
from src.network import generate_network
from src.request_model import (
    RequestTrace,
    generate_request_trace,
    split_requests_chronologically,
)
from src.simulation import (
    MAB_COMPARISON_STRATEGIES,
    evaluate_held_out_mab_comparison,
    run_mab_strategy_comparison,
)


class MABComparisonExperimentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = SimulationConfig(
            seed=31,
            num_files=12,
            num_users=24,
            num_edge_servers=3,
            cache_capacity=4,
            num_requests=500,
            mab_training_fraction=0.60,
            mab_update_interval=25,
        )

    def test_chronological_split_preserves_order_and_rejects_bad_inputs(self) -> None:
        trace = RequestTrace(
            user_ids=np.arange(10, dtype=int) % 2,
            file_ids=np.arange(10, dtype=int),
            file_sizes_mbits=np.ones(10),
            popularity=np.full(10, 0.1),
            user_activity=np.full(2, 0.5),
        )

        request_split = split_requests_chronologically(trace, 0.60)

        np.testing.assert_array_equal(
            request_split.training_file_ids,
            np.arange(6, dtype=int),
        )
        np.testing.assert_array_equal(
            request_split.evaluation_file_ids,
            np.arange(6, 10, dtype=int),
        )
        self.assertEqual(request_split.training_request_count, 6)
        self.assertEqual(request_split.evaluation_request_count, 4)

        for invalid_fraction in (0.0, 1.0, -0.1, float("nan"), "train"):
            with self.subTest(training_fraction=invalid_fraction):
                with self.assertRaises(ValueError):
                    split_requests_chronologically(trace, invalid_fraction)

        short_trace = replace(
            trace,
            user_ids=np.array([0], dtype=int),
            file_ids=np.array([0], dtype=int),
        )
        with self.assertRaisesRegex(ValueError, "at least two requests"):
            split_requests_chronologically(short_trace, 0.60)

    def test_comparison_is_reproducible_fair_and_capacity_feasible(self) -> None:
        first = run_mab_strategy_comparison(self.config)
        second = run_mab_strategy_comparison(self.config)

        pd.testing.assert_frame_equal(first.metrics, second.metrics)
        self.assertEqual(first.final_caches, second.final_caches)
        self.assertTrue(
            np.array_equal(
                first.mab_diagnostics.selection_counts,
                second.mab_diagnostics.selection_counts,
            )
        )
        self.assertTrue(
            np.array_equal(
                first.mab_diagnostics.estimated_mean_rewards_ms,
                second.mab_diagnostics.estimated_mean_rewards_ms,
            )
        )

        self.assertEqual(
            list(first.metrics["strategy"]),
            list(MAB_COMPARISON_STRATEGIES),
        )
        self.assertEqual(first.training_request_count, 300)
        self.assertEqual(first.evaluation_request_count, 200)
        self.assertTrue((first.metrics["training_request_count"] == 300).all())
        self.assertTrue((first.metrics["evaluation_request_count"] == 200).all())
        self.assertTrue((first.metrics["bandwidth_allocation"] == "equal").all())
        self.assertFalse(first.metrics["cache_information"].isna().any())
        self.assertEqual(first.metrics["avg_wireless_rate_mbps"].nunique(), 1)
        self.assertEqual(first.metrics["bandwidth_fairness_index"].nunique(), 1)

        finite_columns = [
            "avg_latency_ms",
            "p95_latency_ms",
            "cache_hit_ratio",
            "backhaul_load_ratio",
            "avg_wireless_rate_mbps",
        ]
        self.assertTrue(np.isfinite(first.metrics[finite_columns]).all().all())
        self.assertTrue(first.metrics["cache_hit_ratio"].between(0.0, 1.0).all())
        self.assertTrue(first.metrics["backhaul_load_ratio"].between(0.0, 1.0).all())

        for caches in first.final_caches.values():
            for cached_files in caches.values():
                used_mbits = float(
                    np.sum(first.file_sizes_mbits[list(cached_files)])
                )
                self.assertLessEqual(
                    used_mbits,
                    self.config.cache_budget_mbits + 1e-9,
                )

        diagnostics = build_mab_diagnostics_record(self.config, first)
        self.assertEqual(
            diagnostics["completed_epochs"],
            math.ceil(300 / self.config.mab_update_interval),
        )
        self.assertGreater(diagnostics["selected_arm_updates"], 0)
        self.assertGreaterEqual(diagnostics["explored_arm_fraction"], 0.0)
        self.assertLessEqual(diagnostics["explored_arm_fraction"], 1.0)
        self.assertGreaterEqual(diagnostics["mean_final_cache_utilization"], 0.0)
        self.assertLessEqual(
            diagnostics["mean_final_cache_utilization"],
            1.0 + 1e-9,
        )

    def test_evaluation_suffix_does_not_change_learned_caches(self) -> None:
        rng = np.random.default_rng(self.config.seed)
        network = generate_network(self.config, rng)
        original_trace = generate_request_trace(self.config, rng, network)
        training_count = int(
            self.config.num_requests * self.config.mab_training_fraction
        )

        changed_user_ids = original_trace.user_ids.copy()
        changed_file_ids = original_trace.file_ids.copy()
        changed_user_ids[training_count:] = 0
        changed_file_ids[training_count:] = (
            changed_file_ids[training_count:] + 1
        ) % self.config.num_files
        changed_trace = replace(
            original_trace,
            user_ids=changed_user_ids,
            file_ids=changed_file_ids,
        )

        original = evaluate_held_out_mab_comparison(
            self.config,
            network,
            original_trace,
        )
        changed = evaluate_held_out_mab_comparison(
            self.config,
            network,
            changed_trace,
        )

        self.assertEqual(original.final_caches, changed.final_caches)
        self.assertTrue(
            np.array_equal(
                original.mab_diagnostics.selection_counts,
                changed.mab_diagnostics.selection_counts,
            )
        )
        self.assertTrue(
            np.array_equal(
                original.mab_diagnostics.estimated_mean_rewards_ms,
                changed.mab_diagnostics.estimated_mean_rewards_ms,
            )
        )
        self.assertFalse(original.metrics.equals(changed.metrics))


if __name__ == "__main__":
    unittest.main()
