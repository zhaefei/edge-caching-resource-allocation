"""Sanity tests for the edge caching simulation.

These tests intentionally focus on basic model validity rather than exact
numeric outputs. They help confirm that future changes preserve core simulation
assumptions.
"""

from __future__ import annotations

import unittest
from dataclasses import replace

import numpy as np

from config import SimulationConfig
from src.caching_algorithms import (
    greedy_latency_aware_caching,
    local_popularity_based_caching,
    popularity_based_caching,
    random_caching,
)
from src.network import generate_network
from src.request_model import generate_request_trace, zipf_probabilities
from src.resource_allocation import (
    demand_aware_bandwidth_allocation,
    equal_bandwidth_allocation,
)
from src.simulation import run_strategy_comparison


class SimulationSanityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = SimulationConfig(
            seed=7,
            num_files=20,
            num_users=30,
            num_edge_servers=4,
            cache_capacity=5,
            num_requests=600,
        )
        self.rng = np.random.default_rng(self.config.seed)
        self.network = generate_network(self.config, self.rng)
        self.trace = generate_request_trace(self.config, self.rng)

    def test_zipf_probabilities_are_valid(self) -> None:
        probabilities = zipf_probabilities(num_items=10, alpha=0.9)

        self.assertAlmostEqual(float(np.sum(probabilities)), 1.0)
        self.assertTrue(np.all(probabilities > 0.0))
        self.assertTrue(np.all(probabilities[:-1] >= probabilities[1:]))

    def test_caching_strategies_respect_capacity(self) -> None:
        caches_to_check = [
            random_caching(self.config, np.random.default_rng(100)),
            popularity_based_caching(self.config, self.trace.popularity),
            local_popularity_based_caching(
                self.config,
                self.network,
                self.trace.user_ids,
                self.trace.file_ids,
            ),
            greedy_latency_aware_caching(
                self.config,
                self.network,
                self.trace.user_ids,
                self.trace.file_ids,
            ),
        ]

        for caches in caches_to_check:
            self.assertEqual(len(caches), self.config.num_edge_servers)
            for cached_files in caches.values():
                self.assertLessEqual(len(cached_files), self.config.cache_capacity)
                self.assertTrue(
                    all(0 <= file_id < self.config.num_files for file_id in cached_files)
                )

    def test_bandwidth_allocation_conserves_server_bandwidth(self) -> None:
        allocations = [
            equal_bandwidth_allocation(self.config, self.network),
            demand_aware_bandwidth_allocation(
                self.config,
                self.network,
                self.trace.user_ids,
            ),
        ]

        for bandwidth in allocations:
            self.assertEqual(len(bandwidth), self.config.num_users)
            self.assertTrue(np.all(bandwidth >= 0.0))

            for server_id in range(self.config.num_edge_servers):
                users = np.where(self.network.associations == server_id)[0]
                if len(users) == 0:
                    continue
                self.assertAlmostEqual(
                    float(np.sum(bandwidth[users])),
                    self.config.bandwidth_hz,
                    places=5,
                )

    def test_strategy_comparison_outputs_reasonable_metrics(self) -> None:
        results = run_strategy_comparison(self.config)

        expected_columns = {
            "strategy",
            "avg_latency_ms",
            "cache_hit_ratio",
            "backhaul_traffic_mbits",
            "backhaul_load_ratio",
            "avg_wireless_rate_mbps",
        }
        self.assertTrue(expected_columns.issubset(set(results.columns)))
        self.assertEqual(len(results), 5)
        self.assertTrue(np.all(results["avg_latency_ms"] > 0.0))
        self.assertTrue(np.all(results["avg_wireless_rate_mbps"] > 0.0))
        self.assertTrue(np.all(results["cache_hit_ratio"].between(0.0, 1.0)))
        self.assertTrue(np.all(results["backhaul_load_ratio"].between(0.0, 1.0)))

    def test_cache_capacity_larger_than_library_is_handled(self) -> None:
        config = replace(self.config, cache_capacity=self.config.num_files + 10)
        caches = popularity_based_caching(config, self.trace.popularity)

        for cached_files in caches.values():
            self.assertEqual(len(cached_files), config.num_files)


if __name__ == "__main__":
    unittest.main()
