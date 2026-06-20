"""Bandwidth allocation policies for users associated with edge servers."""

from __future__ import annotations

import numpy as np

from config import SimulationConfig
from src.network import NetworkState
from src.request_model import user_request_counts


def equal_bandwidth_allocation(
    config: SimulationConfig,
    network: NetworkState,
) -> np.ndarray:
    """Allocate equal bandwidth to users served by the same edge server."""

    bandwidth = np.zeros(config.num_users, dtype=float)

    for server_id in range(config.num_edge_servers):
        users = np.where(network.associations == server_id)[0]
        if len(users) == 0:
            continue
        bandwidth[users] = config.bandwidth_hz / len(users)

    return bandwidth


def demand_aware_bandwidth_allocation(
    config: SimulationConfig,
    network: NetworkState,
    user_ids: np.ndarray,
) -> np.ndarray:
    """Allocate more bandwidth to users that generate more requests.

    This is a simple demand-aware policy, not a full optimization solver. A
    small baseline weight keeps users with few requests from receiving zero
    bandwidth.
    """

    request_counts = user_request_counts(user_ids, config.num_users).astype(float)
    bandwidth = np.zeros(config.num_users, dtype=float)

    for server_id in range(config.num_edge_servers):
        users = np.where(network.associations == server_id)[0]
        if len(users) == 0:
            continue

        local_weights = request_counts[users] + 1.0
        bandwidth[users] = config.bandwidth_hz * local_weights / np.sum(local_weights)

    return bandwidth
