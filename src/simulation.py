"""High-level simulation runner used by main.py and experiment scripts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import SimulationConfig
from src.caching_algorithms import (
    CacheState,
    MABCachingDiagnostics,
    greedy_latency_aware_caching,
    local_popularity_based_caching,
    mab_ucb_caching,
    popularity_based_caching,
    random_caching,
)
from src.metrics import evaluate_strategy
from src.network import NetworkState, generate_network
from src.request_model import (
    RequestTrace,
    generate_request_trace,
    split_requests_chronologically,
)
from src.resource_allocation import (
    demand_aware_bandwidth_allocation,
    equal_bandwidth_allocation,
)


MAB_COMPARISON_STRATEGIES = (
    "Random caching + equal BW",
    "Prior-informed popularity caching + equal BW",
    "Local popularity caching + equal BW",
    "Greedy caching + equal BW",
    "UCB-style MAB caching + equal BW",
)

MAB_COMPARISON_INFORMATION = {
    "Random caching + equal BW": "seeded random baseline",
    "Prior-informed popularity caching + equal BW": "known Zipf prior",
    "Local popularity caching + equal BW": "training prefix",
    "Greedy caching + equal BW": "training prefix",
    "UCB-style MAB caching + equal BW": "selected-arm training feedback",
}


@dataclass(frozen=True)
class MABComparisonResult:
    """Metrics and inspectable state from one held-out caching comparison."""

    metrics: pd.DataFrame
    mab_diagnostics: MABCachingDiagnostics
    final_caches: dict[str, CacheState]
    file_sizes_mbits: np.ndarray
    training_request_count: int
    evaluation_request_count: int


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


def run_mab_strategy_comparison(config: SimulationConfig) -> MABComparisonResult:
    """Generate one scenario and run the dedicated held-out MAB comparison."""

    rng = np.random.default_rng(config.seed)
    network = generate_network(config, rng)
    trace = generate_request_trace(config, rng, network)
    return evaluate_held_out_mab_comparison(config, network, trace)


def evaluate_held_out_mab_comparison(
    config: SimulationConfig,
    network: NetworkState,
    trace: RequestTrace,
) -> MABComparisonResult:
    """Compare fixed caches on a common suffix after training on one prefix."""

    request_split = split_requests_chronologically(
        trace,
        config.mab_training_fraction,
    )
    equal_bandwidth = equal_bandwidth_allocation(config, network)

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
        request_split.training_user_ids,
        request_split.training_file_ids,
        trace.file_sizes_mbits,
    )
    greedy_cache = greedy_latency_aware_caching(
        config,
        network,
        request_split.training_user_ids,
        request_split.training_file_ids,
        trace.file_sizes_mbits,
    )
    mab_cache, mab_diagnostics = mab_ucb_caching(
        config,
        network,
        request_split.training_user_ids,
        request_split.training_file_ids,
        trace.file_sizes_mbits,
        np.random.default_rng(config.seed + config.mab_seed_offset),
    )

    final_caches = {
        MAB_COMPARISON_STRATEGIES[0]: random_cache,
        MAB_COMPARISON_STRATEGIES[1]: popularity_cache,
        MAB_COMPARISON_STRATEGIES[2]: local_popularity_cache,
        MAB_COMPARISON_STRATEGIES[3]: greedy_cache,
        MAB_COMPARISON_STRATEGIES[4]: mab_cache,
    }
    rows = [
        evaluate_strategy(
            strategy_name,
            config,
            network,
            request_split.evaluation_user_ids,
            request_split.evaluation_file_ids,
            trace.file_sizes_mbits,
            final_caches[strategy_name],
            equal_bandwidth,
        )
        for strategy_name in MAB_COMPARISON_STRATEGIES
    ]
    metrics = pd.DataFrame(rows)
    total_requests = (
        request_split.training_request_count
        + request_split.evaluation_request_count
    )
    metrics.insert(
        1,
        "cache_information",
        metrics["strategy"].map(MAB_COMPARISON_INFORMATION),
    )
    metrics.insert(2, "bandwidth_allocation", "equal")
    metrics.insert(
        3,
        "training_request_count",
        request_split.training_request_count,
    )
    metrics.insert(
        4,
        "evaluation_request_count",
        request_split.evaluation_request_count,
    )
    metrics.insert(
        5,
        "actual_training_fraction",
        request_split.training_request_count / total_requests,
    )

    return MABComparisonResult(
        metrics=metrics,
        mab_diagnostics=mab_diagnostics,
        final_caches=final_caches,
        file_sizes_mbits=trace.file_sizes_mbits,
        training_request_count=request_split.training_request_count,
        evaluation_request_count=request_split.evaluation_request_count,
    )
