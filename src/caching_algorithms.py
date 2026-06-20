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
) -> CacheState:
    """Randomly cache files at each edge server as a simple baseline."""

    capacity = min(config.cache_capacity, config.num_files)
    caches: CacheState = {}

    for server_id in range(config.num_edge_servers):
        cached_files = rng.choice(
            config.num_files,
            size=capacity,
            replace=False,
        )
        caches[server_id] = set(int(file_id) for file_id in cached_files)

    return caches


def popularity_based_caching(
    config: SimulationConfig,
    popularity: np.ndarray,
) -> CacheState:
    """Cache the globally most popular files at every edge server."""

    capacity = min(config.cache_capacity, config.num_files)
    most_popular_files = np.argsort(-popularity)[:capacity]

    return {
        server_id: set(int(file_id) for file_id in most_popular_files)
        for server_id in range(config.num_edge_servers)
    }


def local_popularity_based_caching(
    config: SimulationConfig,
    network: NetworkState,
    user_ids: np.ndarray,
    file_ids: np.ndarray,
) -> CacheState:
    """Cache the most requested files observed near each edge server.

    This heuristic uses local demand information. It is still simple enough for
    an undergraduate simulation project, but it captures the idea that different
    edge servers may see slightly different request patterns.
    """

    capacity = min(config.cache_capacity, config.num_files)
    request_servers = network.associations[user_ids]
    caches: CacheState = {}

    for server_id in range(config.num_edge_servers):
        local_files = file_ids[request_servers == server_id]
        local_counts = np.bincount(local_files, minlength=config.num_files)
        most_requested_files = np.argsort(-local_counts)[:capacity]
        caches[server_id] = set(int(file_id) for file_id in most_requested_files)

    return caches


def greedy_latency_aware_caching(
    config: SimulationConfig,
    network: NetworkState,
    user_ids: np.ndarray,
    file_ids: np.ndarray,
) -> CacheState:
    """Greedily cache files that reduce the most backhaul latency.

    A cache hit avoids the fixed backhaul latency and the cloud-to-edge
    transfer time. The greedy step selects the server-file pair with the
    largest estimated latency reduction until all caches are full.
    """

    capacity = min(config.cache_capacity, config.num_files)
    caches: CacheState = {
        server_id: set() for server_id in range(config.num_edge_servers)
    }
    request_servers = network.associations[user_ids]
    backhaul_penalty_ms = backhaul_miss_penalty_ms(config)

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

    for _ in range(config.num_edge_servers * capacity):
        best_server = -1
        best_file = -1
        best_benefit = -1.0

        for server_id in range(config.num_edge_servers):
            if len(caches[server_id]) >= capacity:
                continue

            for file_id in range(config.num_files):
                if file_id in caches[server_id]:
                    continue

                benefit = local_request_counts[server_id, file_id] * backhaul_penalty_ms
                if benefit > best_benefit:
                    best_server = server_id
                    best_file = file_id
                    best_benefit = benefit

        if best_server < 0:
            break

        caches[best_server].add(best_file)

    return caches


def backhaul_miss_penalty_ms(config: SimulationConfig) -> float:
    """Backhaul delay paid when content is not cached at the edge."""

    transfer_time_ms = (config.file_size_mbits / config.backhaul_rate_mbps) * 1000.0
    return config.backhaul_latency_ms + transfer_time_ms
