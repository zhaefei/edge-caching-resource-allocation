"""Performance metrics for caching and resource allocation strategies."""

from __future__ import annotations

from typing import Dict, Set

import numpy as np

from config import SimulationConfig
from src.caching_algorithms import backhaul_miss_penalties_ms
from src.network import NetworkState, compute_user_rates_mbps

CacheState = Dict[int, Set[int]]


def evaluate_strategy(
    strategy_name: str,
    config: SimulationConfig,
    network: NetworkState,
    user_ids: np.ndarray,
    file_ids: np.ndarray,
    file_sizes_mbits: np.ndarray,
    caches: CacheState,
    user_bandwidth_hz: np.ndarray,
) -> dict:
    """Evaluate latency, hit ratio, backhaul load, and wireless rate."""

    user_rates_mbps = compute_user_rates_mbps(config, network, user_bandwidth_hz)
    request_servers = network.associations[user_ids]
    hits = np.array(
        [
            int(file_id) in caches[int(server_id)]
            for file_id, server_id in zip(file_ids, request_servers)
        ],
        dtype=bool,
    )
    request_file_sizes_mbits = file_sizes_mbits[file_ids]

    request_rates = np.maximum(user_rates_mbps[user_ids], 1e-9)
    wireless_delay_ms = (request_file_sizes_mbits / request_rates) * 1000.0
    miss_penalty_ms = backhaul_miss_penalties_ms(config, request_file_sizes_mbits)
    backhaul_delay_ms = np.where(hits, 0.0, miss_penalty_ms)
    total_latency_ms = wireless_delay_ms + backhaul_delay_ms

    total_requests = len(file_ids)
    backhaul_traffic_mbits = float(np.sum(request_file_sizes_mbits[~hits]))

    return {
        "strategy": strategy_name,
        "avg_latency_ms": float(np.mean(total_latency_ms)),
        "median_latency_ms": float(np.median(total_latency_ms)),
        "p95_latency_ms": float(np.percentile(total_latency_ms, 95)),
        "latency_std_ms": float(np.std(total_latency_ms)),
        "cache_hit_ratio": float(np.mean(hits)),
        "backhaul_traffic_mbits": backhaul_traffic_mbits,
        "backhaul_load_ratio": float(np.mean(~hits)),
        "avg_wireless_rate_mbps": float(np.mean(request_rates)),
        "avg_wireless_delay_ms": float(np.mean(wireless_delay_ms)),
        "avg_backhaul_delay_ms": float(np.mean(backhaul_delay_ms)),
        "avg_requested_file_size_mbits": float(np.mean(request_file_sizes_mbits)),
    }
