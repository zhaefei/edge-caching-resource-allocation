"""High-level simulation runner used by main.py and experiment scripts."""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import SimulationConfig
from src.caching_algorithms import (
    greedy_latency_aware_caching,
    local_popularity_based_caching,
    popularity_based_caching,
    random_caching,
)
from src.metrics import evaluate_strategy
from src.network import generate_network
from src.request_model import generate_request_trace
from src.resource_allocation import (
    demand_aware_bandwidth_allocation,
    equal_bandwidth_allocation,
)


def run_strategy_comparison(config: SimulationConfig) -> pd.DataFrame:
    """Run one scenario and compare all implemented strategies fairly."""

    rng = np.random.default_rng(config.seed)
    network = generate_network(config, rng)
    trace = generate_request_trace(config, rng, network)

    equal_bandwidth = equal_bandwidth_allocation(config, network)
    demand_aware_bandwidth = demand_aware_bandwidth_allocation(
        config,
        network,
        trace.user_ids,
    )

    random_cache = random_caching(
        config,
        np.random.default_rng(config.seed + 100),
        trace.file_sizes_mbits,
    )
    popularity_cache = popularity_based_caching(
        config,
        trace.popularity,
        trace.file_sizes_mbits,
    )
    local_popularity_cache = local_popularity_based_caching(
        config,
        network,
        trace.user_ids,
        trace.file_ids,
        trace.file_sizes_mbits,
    )
    greedy_cache = greedy_latency_aware_caching(
        config,
        network,
        trace.user_ids,
        trace.file_ids,
        trace.file_sizes_mbits,
    )

    rows = [
        evaluate_strategy(
            "Random caching + equal BW",
            config,
            network,
            trace.user_ids,
            trace.file_ids,
            trace.file_sizes_mbits,
            random_cache,
            equal_bandwidth,
        ),
        evaluate_strategy(
            "Popularity caching + equal BW",
            config,
            network,
            trace.user_ids,
            trace.file_ids,
            trace.file_sizes_mbits,
            popularity_cache,
            equal_bandwidth,
        ),
        evaluate_strategy(
            "Local popularity caching + equal BW",
            config,
            network,
            trace.user_ids,
            trace.file_ids,
            trace.file_sizes_mbits,
            local_popularity_cache,
            equal_bandwidth,
        ),
        evaluate_strategy(
            "Greedy caching + equal BW",
            config,
            network,
            trace.user_ids,
            trace.file_ids,
            trace.file_sizes_mbits,
            greedy_cache,
            equal_bandwidth,
        ),
        evaluate_strategy(
            "Greedy caching + demand-aware BW",
            config,
            network,
            trace.user_ids,
            trace.file_ids,
            trace.file_sizes_mbits,
            greedy_cache,
            demand_aware_bandwidth,
        ),
    ]

    return pd.DataFrame(rows)
