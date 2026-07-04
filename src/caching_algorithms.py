"""Caching strategies for edge servers with limited cache capacity."""

from __future__ import annotations

from typing import Dict, Set

import numpy as np

from config import SimulationConfig
from src.network import NetworkState

CacheState = Dict[int, Set[int]]


def random_caching(
    config: SimulationConfig,
    rng: np.random.Generator,
    file_sizes_mbits: np.ndarray,
) -> CacheState:
    """Randomly cache files at each edge server as a simple baseline."""

    caches: CacheState = {}

    for server_id in range(config.num_edge_servers):
        candidate_files = rng.permutation(config.num_files)
        caches[server_id] = _select_ordered_files_within_budget(
            candidate_files,
            file_sizes_mbits,
            config.cache_budget_mbits,
        )

    return caches


def popularity_based_caching(
    config: SimulationConfig,
    popularity: np.ndarray,
    file_sizes_mbits: np.ndarray,
) -> CacheState:
    """Cache the globally most popular files at every edge server."""

    most_popular_files = np.lexsort((file_sizes_mbits, -popularity))

    return {
        server_id: _select_ordered_files_within_budget(
            most_popular_files,
            file_sizes_mbits,
            config.cache_budget_mbits,
        )
        for server_id in range(config.num_edge_servers)
    }


def local_popularity_based_caching(
    config: SimulationConfig,
    network: NetworkState,
    user_ids: np.ndarray,
    file_ids: np.ndarray,
    file_sizes_mbits: np.ndarray,
) -> CacheState:
    """Cache the most requested files observed near each edge server.

    This heuristic uses local demand information. It is still simple enough for
    an undergraduate simulation project, but it captures the idea that different
    edge servers may see slightly different request patterns.
    """

    request_servers = network.associations[user_ids]
    caches: CacheState = {}

    for server_id in range(config.num_edge_servers):
        local_files = file_ids[request_servers == server_id]
        local_counts = np.bincount(local_files, minlength=config.num_files)
        most_requested_files = np.lexsort((file_sizes_mbits, -local_counts))
        caches[server_id] = _select_ordered_files_within_budget(
            most_requested_files,
            file_sizes_mbits,
            config.cache_budget_mbits,
        )

    return caches


def greedy_latency_aware_caching(
    config: SimulationConfig,
    network: NetworkState,
    user_ids: np.ndarray,
    file_ids: np.ndarray,
    file_sizes_mbits: np.ndarray,
) -> CacheState:
    """Greedily cache files that reduce the most backhaul latency.

    A cache hit avoids the fixed backhaul latency and the cloud-to-edge
    transfer time. The greedy step selects the server-file pair with the
    largest estimated latency reduction until all caches are full.
    """

    caches: CacheState = {}
    request_servers = network.associations[user_ids]
    backhaul_penalties_ms = backhaul_miss_penalties_ms(config, file_sizes_mbits)

    local_request_counts = np.zeros(
        (config.num_edge_servers, config.num_files),
        dtype=int,
    )
    for server_id in range(config.num_edge_servers):
        local_files = file_ids[request_servers == server_id]
        local_request_counts[server_id] = np.bincount(
            local_files,
            minlength=config.num_files,
        )

    for server_id in range(config.num_edge_servers):
        local_benefits = local_request_counts[server_id] * backhaul_penalties_ms
        benefit_density = np.divide(
            local_benefits,
            file_sizes_mbits,
            out=np.zeros_like(local_benefits, dtype=float),
            where=file_sizes_mbits > 0.0,
        )
        candidate_files = np.lexsort((file_sizes_mbits, -benefit_density))
        caches[server_id] = _select_ordered_files_within_budget(
            candidate_files,
            file_sizes_mbits,
            config.cache_budget_mbits,
        )

    return caches


def backhaul_miss_penalties_ms(
    config: SimulationConfig,
    file_sizes_mbits: np.ndarray,
) -> np.ndarray:
    """Backhaul delay paid when content is not cached at the edge."""

    transfer_time_ms = (file_sizes_mbits / config.backhaul_rate_mbps) * 1000.0
    return config.backhaul_latency_ms + transfer_time_ms


def _select_ordered_files_within_budget(
    candidate_files: np.ndarray,
    file_sizes_mbits: np.ndarray,
    cache_budget_mbits: float,
) -> Set[int]:
    """Greedily pack files in the provided order under a size budget."""

    selected: Set[int] = set()
    used_budget_mbits = 0.0

    for file_id in candidate_files:
        file_id = int(file_id)
        file_size_mbits = float(file_sizes_mbits[file_id])
        if used_budget_mbits + file_size_mbits > cache_budget_mbits + 1e-9:
            continue

        selected.add(file_id)
        used_budget_mbits += file_size_mbits

    return selected
