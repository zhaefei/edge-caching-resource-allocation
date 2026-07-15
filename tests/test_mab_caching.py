"""Focused tests for the lightweight UCB-style caching policy."""

from __future__ import annotations

from dataclasses import replace
import math
import unittest

import numpy as np

from config import SimulationConfig
from src.caching_algorithms import _incremental_mean, mab_ucb_caching
from src.network import NetworkState, generate_network
from src.request_model import generate_request_trace


class MABUCBPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = SimulationConfig(
            seed=19,
            num_files=12,
            num_users=24,
            num_edge_servers=3,
            cache_capacity=4,
            num_requests=480,
            mab_update_interval=40,
        )
        request_rng = np.random.default_rng(self.config.seed)
        self.network = generate_network(self.config, request_rng)
        self.trace = generate_request_trace(
            self.config,
            request_rng,
            self.network,
        )
        training_count = int(
            self.config.mab_training_fraction * self.config.num_requests
        )
        self.training_user_ids = self.trace.user_ids[:training_count]
        self.training_file_ids = self.trace.file_ids[:training_count]

    def test_fixed_seed_is_reproducible_and_respects_cache_budget(self) -> None:
        seed = self.config.seed + self.config.mab_seed_offset
        first_caches, first_diagnostics = mab_ucb_caching(
            self.config,
            self.network,
            self.training_user_ids,
            self.training_file_ids,
            self.trace.file_sizes_mbits,
            np.random.default_rng(seed),
        )
        second_caches, second_diagnostics = mab_ucb_caching(
            self.config,
            self.network,
            self.training_user_ids,
            self.training_file_ids,
            self.trace.file_sizes_mbits,
            np.random.default_rng(seed),
        )

        self.assertEqual(first_caches, second_caches)
        self.assertTrue(
            np.array_equal(
                first_diagnostics.selection_counts,
                second_diagnostics.selection_counts,
            )
        )
        self.assertTrue(
            np.array_equal(
                first_diagnostics.estimated_mean_rewards_ms,
                second_diagnostics.estimated_mean_rewards_ms,
            )
        )
        self.assertEqual(
            first_diagnostics.completed_epochs,
            math.ceil(len(self.training_file_ids) / self.config.mab_update_interval),
        )
        self.assertEqual(
            first_diagnostics.selection_counts.shape,
            (self.config.num_edge_servers, self.config.num_files),
        )
        self.assertEqual(
            first_diagnostics.estimated_mean_rewards_ms.shape,
            (self.config.num_edge_servers, self.config.num_files),
        )
        self.assertTrue(
            np.all(np.isfinite(first_diagnostics.estimated_mean_rewards_ms))
        )
        self.assertGreaterEqual(first_diagnostics.explored_arm_fraction, 0.0)
        self.assertLessEqual(first_diagnostics.explored_arm_fraction, 1.0)
        cacheable_files = (
            self.trace.file_sizes_mbits <= self.config.cache_budget_mbits + 1e-9
        )
        self.assertAlmostEqual(
            first_diagnostics.explored_arm_fraction,
            float(
                np.mean(
                    first_diagnostics.selection_counts[:, cacheable_files] > 0
                )
            ),
        )

        for cached_files in first_caches.values():
            cached_size_mbits = float(
                np.sum(self.trace.file_sizes_mbits[list(cached_files)])
            )
            self.assertLessEqual(
                cached_size_mbits,
                self.config.cache_budget_mbits + 1e-9,
            )
            self.assertTrue(
                all(0 <= file_id < self.config.num_files for file_id in cached_files)
            )

    def test_policy_learns_repeated_high_reward_file(self) -> None:
        config = SimulationConfig(
            seed=5,
            num_files=4,
            num_users=1,
            num_edge_servers=1,
            cache_capacity=1,
            num_requests=120,
            file_size_mbits=5.0,
            file_size_sigma=0.0,
            mab_update_interval=10,
        )
        network = _single_association_network(config)
        user_ids = np.zeros(config.num_requests, dtype=int)
        file_ids = np.zeros(config.num_requests, dtype=int)
        file_sizes_mbits = np.full(config.num_files, 5.0)

        caches, diagnostics = mab_ucb_caching(
            config,
            network,
            user_ids,
            file_ids,
            file_sizes_mbits,
            np.random.default_rng(config.seed + config.mab_seed_offset),
        )

        expected_reward_ms = (
            config.backhaul_latency_ms
            + file_sizes_mbits[0] / config.backhaul_rate_mbps * 1000.0
        )
        self.assertEqual(caches[0], {0})
        self.assertAlmostEqual(
            float(diagnostics.estimated_mean_rewards_ms[0, 0]),
            expected_reward_ms,
        )
        self.assertGreater(
            diagnostics.selection_counts[0, 0],
            diagnostics.selection_counts[0, 1],
        )

    def test_empty_local_demand_and_oversized_files_remain_well_defined(self) -> None:
        config = SimulationConfig(
            seed=3,
            num_files=4,
            num_users=1,
            num_edge_servers=2,
            cache_capacity=1,
            num_requests=20,
            file_size_mbits=5.0,
            file_size_sigma=0.0,
            mab_update_interval=5,
        )
        network = _single_association_network(config)
        user_ids = np.zeros(config.num_requests, dtype=int)
        file_ids = np.resize(np.array([1, 2, 3], dtype=int), config.num_requests)
        file_sizes_mbits = np.array([20.0, 5.0, 5.0, 5.0])

        caches, diagnostics = mab_ucb_caching(
            config,
            network,
            user_ids,
            file_ids,
            file_sizes_mbits,
            np.random.default_rng(config.seed + config.mab_seed_offset),
        )

        self.assertNotIn(0, caches[0])
        self.assertNotIn(0, caches[1])
        self.assertTrue(
            np.all(np.isfinite(diagnostics.estimated_mean_rewards_ms[1]))
        )
        self.assertTrue(
            np.allclose(diagnostics.estimated_mean_rewards_ms[1], 0.0)
        )
        self.assertEqual(int(diagnostics.selection_counts[:, 0].sum()), 0)
        self.assertEqual(diagnostics.explored_arm_fraction, 1.0)

    def test_unselected_requested_arm_receives_no_reward_update(self) -> None:
        config = SimulationConfig(
            seed=8,
            num_files=2,
            num_users=1,
            num_edge_servers=1,
            cache_capacity=1,
            num_requests=10,
            file_size_mbits=5.0,
            file_size_sigma=0.0,
            mab_update_interval=10,
        )
        network = _single_association_network(config)
        policy_seed = config.seed + config.mab_seed_offset
        selected_file = int(np.random.default_rng(policy_seed).permutation(2)[0])
        requested_file = 1 - selected_file

        _, diagnostics = mab_ucb_caching(
            config,
            network,
            np.zeros(config.num_requests, dtype=int),
            np.full(config.num_requests, requested_file, dtype=int),
            np.full(config.num_files, 5.0),
            np.random.default_rng(policy_seed),
        )

        self.assertEqual(diagnostics.selection_counts[0, selected_file], 1)
        self.assertEqual(diagnostics.selection_counts[0, requested_file], 0)
        self.assertEqual(
            diagnostics.estimated_mean_rewards_ms[0, requested_file],
            0.0,
        )

    def test_empty_training_trace_returns_untrained_fixed_caches(self) -> None:
        config = replace(self.config, num_requests=0)
        caches, diagnostics = mab_ucb_caching(
            config,
            self.network,
            np.array([], dtype=int),
            np.array([], dtype=int),
            self.trace.file_sizes_mbits,
            np.random.default_rng(config.seed + config.mab_seed_offset),
        )

        self.assertEqual(set(caches), set(range(config.num_edge_servers)))
        self.assertEqual(diagnostics.completed_epochs, 0)
        self.assertEqual(diagnostics.explored_arm_fraction, 0.0)
        self.assertTrue(np.all(diagnostics.selection_counts == 0))
        self.assertTrue(np.all(diagnostics.estimated_mean_rewards_ms == 0.0))

    def test_incremental_mean_matches_hand_calculation(self) -> None:
        self.assertAlmostEqual(_incremental_mean(10.0, 16.0, 3), 12.0)
        with self.assertRaisesRegex(ValueError, "new_count must be positive"):
            _incremental_mean(10.0, 16.0, 0)

    def test_invalid_hyperparameters_are_rejected(self) -> None:
        invalid_configs = [
            replace(self.config, mab_update_interval=0),
            replace(self.config, mab_update_interval=2.5),
            replace(self.config, mab_exploration_weight=-0.1),
            replace(self.config, mab_exploration_weight=float("nan")),
            replace(self.config, mab_exploration_weight=float("inf")),
            replace(self.config, mab_exploration_weight="wide"),
            replace(self.config, mab_training_fraction=1.0),
            replace(self.config, mab_training_fraction=float("nan")),
            replace(self.config, mab_training_fraction="all"),
            replace(self.config, backhaul_rate_mbps=0.0),
            replace(self.config, backhaul_latency_ms=-1.0),
            replace(self.config, cache_capacity=-1),
        ]

        for config in invalid_configs:
            with self.subTest(config=config):
                with self.assertRaises(ValueError):
                    mab_ucb_caching(
                        config,
                        self.network,
                        self.training_user_ids,
                        self.training_file_ids,
                        self.trace.file_sizes_mbits,
                        np.random.default_rng(1),
                    )

    def test_invalid_request_and_network_inputs_are_rejected(self) -> None:
        bad_network = replace(
            self.network,
            associations=np.full(
                self.config.num_users,
                self.config.num_edge_servers,
                dtype=int,
            ),
        )
        cases = [
            (
                self.network,
                self.training_user_ids,
                self.training_file_ids[:-1],
                self.trace.file_sizes_mbits,
                "equal length",
            ),
            (
                self.network,
                self.training_user_ids.astype(float) + 0.5,
                self.training_file_ids,
                self.trace.file_sizes_mbits,
                "must be integers",
            ),
            (
                self.network,
                self.training_user_ids,
                self.training_file_ids,
                np.zeros(self.config.num_files),
                "finite positive values",
            ),
            (
                bad_network,
                self.training_user_ids,
                self.training_file_ids,
                self.trace.file_sizes_mbits,
                "unknown edge server",
            ),
        ]

        for network, user_ids, file_ids, file_sizes, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    mab_ucb_caching(
                        self.config,
                        network,
                        user_ids,
                        file_ids,
                        file_sizes,
                        np.random.default_rng(1),
                    )


def _single_association_network(config: SimulationConfig) -> NetworkState:
    """Build the minimal network state needed by the caching learner."""

    return NetworkState(
        user_positions=np.zeros((config.num_users, 2), dtype=float),
        server_positions=np.zeros((config.num_edge_servers, 2), dtype=float),
        associations=np.zeros(config.num_users, dtype=int),
        channel_gains=np.ones(
            (config.num_users, config.num_edge_servers),
            dtype=float,
        ),
        channel_model_name="test",
    )


if __name__ == "__main__":
    unittest.main()
