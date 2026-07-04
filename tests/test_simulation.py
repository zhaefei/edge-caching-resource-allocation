"""Sanity tests for the edge caching simulation.

These tests intentionally focus on basic model validity rather than exact
numeric outputs. They help confirm that future changes preserve core simulation
assumptions.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
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
from src.metrics import evaluate_strategy, jain_fairness_index
from src.network import generate_network
from src.request_model import (
    build_server_popularity_profiles,
    generate_file_size_profile,
    generate_request_trace,
    zipf_probabilities,
)
from src.reproducibility import write_run_metadata
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
        self.trace = generate_request_trace(self.config, self.rng, self.network)

    def test_zipf_probabilities_are_valid(self) -> None:
        probabilities = zipf_probabilities(num_items=10, alpha=0.9)

        self.assertAlmostEqual(float(np.sum(probabilities)), 1.0)
        self.assertTrue(np.all(probabilities > 0.0))
        self.assertTrue(np.all(probabilities[:-1] >= probabilities[1:]))

    def test_caching_strategies_respect_capacity(self) -> None:
        file_sizes = self.trace.file_sizes_mbits
        caches_to_check = [
            random_caching(self.config, np.random.default_rng(100), file_sizes),
            popularity_based_caching(self.config, self.trace.popularity, file_sizes),
            local_popularity_based_caching(
                self.config,
                self.network,
                self.trace.user_ids,
                self.trace.file_ids,
                file_sizes,
            ),
            greedy_latency_aware_caching(
                self.config,
                self.network,
                self.trace.user_ids,
                self.trace.file_ids,
                file_sizes,
            ),
        ]

        for caches in caches_to_check:
            self.assertEqual(len(caches), self.config.num_edge_servers)
            for cached_files in caches.values():
                cached_budget = float(np.sum(file_sizes[list(cached_files)]))
                self.assertLessEqual(
                    cached_budget,
                    self.config.cache_budget_mbits + 1e-9,
                )
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

    def test_jain_fairness_index_bounds(self) -> None:
        self.assertAlmostEqual(jain_fairness_index(np.array([1.0, 1.0, 1.0])), 1.0)
        self.assertGreater(jain_fairness_index(np.array([3.0, 1.0, 0.0])), 0.0)
        self.assertLessEqual(jain_fairness_index(np.array([3.0, 1.0, 0.0])), 1.0)
        self.assertEqual(jain_fairness_index(np.array([0.0, 0.0])), 0.0)

    def test_strategy_comparison_outputs_reasonable_metrics(self) -> None:
        results = run_strategy_comparison(self.config)

        expected_columns = {
            "strategy",
            "avg_latency_ms",
            "median_latency_ms",
            "p95_latency_ms",
            "latency_std_ms",
            "cache_hit_ratio",
            "backhaul_traffic_mbits",
            "backhaul_load_ratio",
            "avg_wireless_rate_mbps",
            "bandwidth_fairness_index",
            "wireless_rate_fairness_index",
        }
        self.assertTrue(expected_columns.issubset(set(results.columns)))
        self.assertEqual(len(results), 5)
        self.assertTrue(np.all(results["avg_latency_ms"] > 0.0))
        self.assertTrue(np.all(results["p95_latency_ms"] >= results["avg_latency_ms"]))
        self.assertTrue(np.all(results["latency_std_ms"] >= 0.0))
        self.assertTrue(np.all(results["avg_wireless_rate_mbps"] > 0.0))
        self.assertTrue(np.all(results["cache_hit_ratio"].between(0.0, 1.0)))
        self.assertTrue(np.all(results["backhaul_load_ratio"].between(0.0, 1.0)))
        self.assertTrue(np.all(results["bandwidth_fairness_index"].between(0.0, 1.0)))
        self.assertTrue(np.all(results["wireless_rate_fairness_index"].between(0.0, 1.0)))

    def test_cache_capacity_larger_than_library_is_handled(self) -> None:
        config = replace(self.config, cache_capacity=self.config.num_files + 10)
        caches = popularity_based_caching(
            config,
            self.trace.popularity,
            self.trace.file_sizes_mbits,
        )

        for cached_files in caches.values():
            self.assertEqual(len(cached_files), config.num_files)

    def test_file_size_profile_matches_target_scale(self) -> None:
        config = replace(
            self.config,
            num_files=200,
            file_size_mbits=5.0,
            file_size_sigma=0.8,
            min_file_size_mbits=1.0,
            max_file_size_mbits=12.0,
        )
        sizes = generate_file_size_profile(config, np.random.default_rng(config.seed))

        self.assertEqual(len(sizes), config.num_files)
        self.assertTrue(np.all(sizes >= config.min_file_size_mbits))
        self.assertTrue(np.all(sizes <= config.max_file_size_mbits))
        self.assertLess(abs(float(np.mean(sizes)) - config.file_size_mbits), 0.3)

    def test_server_popularity_profiles_boost_distinct_file_groups(self) -> None:
        config = replace(
            self.config,
            num_files=24,
            num_edge_servers=4,
            spatial_locality_strength=0.8,
            local_preference_boost=5.0,
        )
        global_popularity = zipf_probabilities(config.num_files, config.zipf_alpha)
        profiles = build_server_popularity_profiles(config, global_popularity)
        file_groups = np.array_split(np.arange(config.num_files), config.num_edge_servers)

        self.assertEqual(profiles.shape, (config.num_edge_servers, config.num_files))
        self.assertTrue(np.allclose(np.sum(profiles, axis=1), 1.0))

        for server_id, preferred_files in enumerate(file_groups):
            preferred_mass = float(np.sum(profiles[server_id, preferred_files]))
            global_mass = float(np.sum(global_popularity[preferred_files]))
            self.assertGreater(preferred_mass, global_mass)

    def test_local_popularity_caching_benefits_from_spatial_locality(self) -> None:
        config = SimulationConfig(
            seed=11,
            num_files=24,
            num_users=40,
            num_edge_servers=4,
            cache_capacity=4,
            num_requests=4000,
            spatial_locality_strength=0.85,
            local_preference_boost=6.0,
        )
        rng = np.random.default_rng(config.seed)
        network = generate_network(config, rng)
        trace = generate_request_trace(config, rng, network)
        equal_bandwidth = equal_bandwidth_allocation(config, network)

        file_sizes = trace.file_sizes_mbits
        global_cache = popularity_based_caching(config, trace.popularity, file_sizes)
        local_cache = local_popularity_based_caching(
            config,
            network,
            trace.user_ids,
            trace.file_ids,
            file_sizes,
        )

        global_metrics = evaluate_strategy(
            "global",
            config,
            network,
            trace.user_ids,
            trace.file_ids,
            file_sizes,
            global_cache,
            equal_bandwidth,
        )
        local_metrics = evaluate_strategy(
            "local",
            config,
            network,
            trace.user_ids,
            trace.file_ids,
            file_sizes,
            local_cache,
            equal_bandwidth,
        )

        self.assertGreater(
            local_metrics["cache_hit_ratio"],
            global_metrics["cache_hit_ratio"] + 0.05,
        )
        self.assertLess(
            local_metrics["avg_latency_ms"],
            global_metrics["avg_latency_ms"],
        )

    def test_metrics_account_for_variable_file_sizes(self) -> None:
        config = replace(self.config, num_users=2, num_edge_servers=1, num_requests=2)
        network = generate_network(config, np.random.default_rng(config.seed))
        user_ids = np.array([0, 1], dtype=int)
        file_ids = np.array([0, 1], dtype=int)
        file_sizes = np.array([2.0, 8.0], dtype=float)
        user_bandwidth = np.full(config.num_users, config.bandwidth_hz / config.num_users)
        caches = {0: {0}}

        metrics = evaluate_strategy(
            "manual",
            config,
            network,
            user_ids,
            file_ids,
            file_sizes,
            caches,
            user_bandwidth,
        )

        self.assertAlmostEqual(metrics["cache_hit_ratio"], 0.5)
        self.assertAlmostEqual(metrics["backhaul_traffic_mbits"], 8.0)
        self.assertAlmostEqual(metrics["avg_requested_file_size_mbits"], 5.0)
        self.assertAlmostEqual(metrics["bandwidth_fairness_index"], 1.0)

    def test_run_metadata_is_written_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "metadata.json"
            write_run_metadata(self.config, output_path, run_name="unit_test")

            metadata = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(metadata["run_name"], "unit_test")
        self.assertEqual(metadata["config"]["seed"], self.config.seed)
        self.assertIn("python_version", metadata)
        self.assertIn("git_commit", metadata)


if __name__ == "__main__":
    unittest.main()
