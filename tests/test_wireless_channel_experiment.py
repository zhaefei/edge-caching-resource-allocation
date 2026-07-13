"""Tests for the controlled wireless channel sensitivity experiment."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from config import SimulationConfig
from experiments.run_wireless_channel_experiment import (
    CHANNEL_MODEL_LABELS,
    FOCAL_STRATEGY,
    prepare_focal_channel_results,
    run_wireless_channel_experiment,
)


class WirelessChannelExperimentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = SimulationConfig(
            seed=23,
            num_files=16,
            num_users=24,
            num_edge_servers=4,
            cache_capacity=4,
            num_requests=300,
        )

    def test_experiment_is_reproducible_and_structured(self) -> None:
        exponents = [3.0, 3.8]
        channel_models = ["path_loss", "path_loss_fading"]

        first = run_wireless_channel_experiment(
            self.config,
            path_loss_exponents=exponents,
            channel_models=channel_models,
        )
        second = run_wireless_channel_experiment(
            self.config,
            path_loss_exponents=exponents,
            channel_models=channel_models,
        )

        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(len(first), 20)
        self.assertEqual(set(first["path_loss_exponent"]), set(exponents))
        self.assertEqual(set(first["wireless_channel_model"]), set(channel_models))
        self.assertTrue(np.isfinite(first["avg_latency_ms"]).all())
        self.assertTrue(np.isfinite(first["avg_wireless_rate_mbps"]).all())

    def test_focal_results_compare_only_channel_models(self) -> None:
        results = run_wireless_channel_experiment(
            self.config,
            path_loss_exponents=[3.0, 3.8],
        )

        focal_results = prepare_focal_channel_results(results)

        self.assertEqual(len(focal_results), 4)
        self.assertEqual(
            set(focal_results["strategy"]),
            set(CHANNEL_MODEL_LABELS.values()),
        )
        self.assertTrue((results["strategy"] == FOCAL_STRATEGY).any())


if __name__ == "__main__":
    unittest.main()
