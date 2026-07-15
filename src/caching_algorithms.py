"""Caching strategies for edge servers with limited cache capacity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set

import numpy as np

from config import SimulationConfig
from src.network import NetworkState

CacheState = Dict[int, Set[int]]


@dataclass(frozen=True)
class MABCachingDiagnostics:
    """Inspectable learning statistics from UCB-style cache training."""

    selection_counts: np.ndarray
    estimated_mean_rewards_ms: np.ndarray
    completed_epochs: int
    explored_arm_fraction: float


def mab_ucb_caching(
    config: SimulationConfig,
    network: NetworkState,
    training_user_ids: np.ndarray,
    training_file_ids: np.ndarray,
    file_sizes_mbits: np.ndarray,
    rng: np.random.Generator,
) -> tuple[CacheState, MABCachingDiagnostics]:
    """Learn independent per-server caches with a simple UCB heuristic.

    Each server treats a content file as one arm. At the start of every
    training epoch, untried files receive exploration priority; tried files are
    ranked by their estimated avoided backhaul latency plus a UCB exploration
    bonus. Files are greedily packed by score per Mbit. Only files placed in a
    cache receive a reward update, which makes this a combinatorial semi-bandit
    baseline rather than a full-information popularity estimator.

    The returned cache is a fixed exploitation cache ranked by learned mean
    reward per Mbit. Callers are responsible for passing training requests only
    and evaluating this final cache on a separate held-out request segment.
    """

    training_user_ids = np.asarray(training_user_ids)
    training_file_ids = np.asarray(training_file_ids)
    file_sizes_mbits = np.asarray(file_sizes_mbits, dtype=float)
    _validate_mab_inputs(
        config,
        network,
        training_user_ids,
        training_file_ids,
        file_sizes_mbits,
    )
    training_user_ids = training_user_ids.astype(int, copy=False)
    training_file_ids = training_file_ids.astype(int, copy=False)

    num_servers = config.num_edge_servers
    num_files = config.num_files
    selection_counts = np.zeros((num_servers, num_files), dtype=int)
    mean_rewards_ms = np.zeros((num_servers, num_files), dtype=float)
    backhaul_penalties_ms = backhaul_miss_penalties_ms(config, file_sizes_mbits)

    # Each server gets a stable seeded tie order. This avoids silently favoring
    # low file identifiers when several arms have the same UCB score.
    tie_ranks = np.empty((num_servers, num_files), dtype=int)
    for server_id in range(num_servers):
        tie_order = rng.permutation(num_files)
        tie_ranks[server_id, tie_order] = np.arange(num_files)

    request_servers = network.associations[training_user_ids]
    completed_epochs = 0

    for epoch_start in range(0, len(training_file_ids), config.mab_update_interval):
        epoch_stop = min(
            epoch_start + config.mab_update_interval,
            len(training_file_ids),
        )
        epoch_files = training_file_ids[epoch_start:epoch_stop]
        epoch_servers = request_servers[epoch_start:epoch_stop]
        completed_epochs += 1

        for server_id in range(num_servers):
            counts = selection_counts[server_id]
            rewards = mean_rewards_ms[server_id]
            ucb_scores = np.full(num_files, np.inf, dtype=float)
            tried_arms = counts > 0
            ucb_scores[tried_arms] = rewards[tried_arms] + (
                config.mab_exploration_weight
                * np.sqrt(
                    np.log(completed_epochs + 1.0) / counts[tried_arms]
                )
            )
            score_density = ucb_scores / file_sizes_mbits
            candidate_files = np.lexsort(
                (tie_ranks[server_id], -score_density)
            )
            selected_files = _select_ordered_files_within_budget(
                candidate_files,
                file_sizes_mbits,
                config.cache_budget_mbits,
            )

            local_epoch_files = epoch_files[epoch_servers == server_id]
            local_request_count = len(local_epoch_files)
            local_file_counts = np.bincount(
                local_epoch_files,
                minlength=num_files,
            )

            for file_id in selected_files:
                observed_reward_ms = (
                    float(local_file_counts[file_id])
                    / max(1, local_request_count)
                    * float(backhaul_penalties_ms[file_id])
                )
                selection_counts[server_id, file_id] += 1
                new_count = int(selection_counts[server_id, file_id])
                mean_rewards_ms[server_id, file_id] = _incremental_mean(
                    float(mean_rewards_ms[server_id, file_id]),
                    observed_reward_ms,
                    new_count,
                )

    caches: CacheState = {}
    for server_id in range(num_servers):
        exploitation_density = mean_rewards_ms[server_id] / file_sizes_mbits
        candidate_files = np.lexsort(
            (tie_ranks[server_id], -exploitation_density)
        )
        caches[server_id] = _select_ordered_files_within_budget(
            candidate_files,
            file_sizes_mbits,
            config.cache_budget_mbits,
        )

    cacheable_files = file_sizes_mbits <= config.cache_budget_mbits + 1e-9
    cacheable_arm_count = int(num_servers * np.sum(cacheable_files))
    explored_cacheable_arms = int(
        np.sum(selection_counts[:, cacheable_files] > 0)
    )
    explored_arm_fraction = (
        explored_cacheable_arms / cacheable_arm_count
        if cacheable_arm_count > 0
        else 0.0
    )
    diagnostics = MABCachingDiagnostics(
        selection_counts=selection_counts,
        estimated_mean_rewards_ms=mean_rewards_ms,
        completed_epochs=completed_epochs,
        explored_arm_fraction=float(explored_arm_fraction),
    )
    return caches, diagnostics


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


def _validate_mab_inputs(
    config: SimulationConfig,
    network: NetworkState,
    training_user_ids: np.ndarray,
    training_file_ids: np.ndarray,
    file_sizes_mbits: np.ndarray,
) -> None:
    """Reject malformed MAB inputs before array indexing or training."""

    if config.num_edge_servers <= 0 or config.num_files <= 0:
        raise ValueError("MAB caching requires positive server and file counts")
    if (
        isinstance(config.mab_update_interval, (bool, np.bool_))
        or not isinstance(config.mab_update_interval, (int, np.integer))
        or config.mab_update_interval <= 0
    ):
        raise ValueError("mab_update_interval must be a positive integer")
    numeric_types = (int, float, np.integer, np.floating)
    if (
        isinstance(config.mab_exploration_weight, (bool, np.bool_))
        or not isinstance(config.mab_exploration_weight, numeric_types)
        or not np.isfinite(config.mab_exploration_weight)
        or config.mab_exploration_weight < 0.0
    ):
        raise ValueError("mab_exploration_weight must be finite and non-negative")
    if (
        isinstance(config.mab_training_fraction, (bool, np.bool_))
        or not isinstance(config.mab_training_fraction, numeric_types)
        or not np.isfinite(config.mab_training_fraction)
        or not 0.0 < config.mab_training_fraction < 1.0
    ):
        raise ValueError("mab_training_fraction must be strictly between 0 and 1")
    if (
        not np.isfinite(config.backhaul_rate_mbps)
        or config.backhaul_rate_mbps <= 0.0
    ):
        raise ValueError("backhaul_rate_mbps must be finite and positive")
    if (
        not np.isfinite(config.backhaul_latency_ms)
        or config.backhaul_latency_ms < 0.0
    ):
        raise ValueError("backhaul_latency_ms must be finite and non-negative")
    if (
        not np.isfinite(config.cache_budget_mbits)
        or config.cache_budget_mbits < 0.0
    ):
        raise ValueError("MAB cache budget must be finite and non-negative")
    if network.associations.shape != (config.num_users,):
        raise ValueError("network associations must contain one entry per user")
    if not np.issubdtype(network.associations.dtype, np.integer):
        raise ValueError("network associations must contain integer server IDs")
    if np.any(network.associations < 0) or np.any(
        network.associations >= config.num_edge_servers
    ):
        raise ValueError("network associations reference an unknown edge server")
    if training_user_ids.ndim != 1 or training_file_ids.ndim != 1:
        raise ValueError("MAB training request arrays must be one-dimensional")
    if len(training_user_ids) != len(training_file_ids):
        raise ValueError("MAB training user and file arrays must have equal length")
    if len(training_user_ids) > 0 and not np.issubdtype(
        training_user_ids.dtype,
        np.integer,
    ):
        raise ValueError("MAB training user identifiers must be integers")
    if len(training_file_ids) > 0 and not np.issubdtype(
        training_file_ids.dtype,
        np.integer,
    ):
        raise ValueError("MAB training file identifiers must be integers")
    if file_sizes_mbits.shape != (config.num_files,):
        raise ValueError("file_sizes_mbits must contain one size per content file")
    if not np.all(np.isfinite(file_sizes_mbits)) or np.any(
        file_sizes_mbits <= 0.0
    ):
        raise ValueError("file_sizes_mbits must contain finite positive values")
    if np.any(training_user_ids < 0) or np.any(
        training_user_ids >= len(network.associations)
    ):
        raise ValueError("MAB training user identifiers are out of range")
    if np.any(training_file_ids < 0) or np.any(
        training_file_ids >= config.num_files
    ):
        raise ValueError("MAB training file identifiers are out of range")


def _incremental_mean(
    previous_mean: float,
    observation: float,
    new_count: int,
) -> float:
    """Update a running mean after adding one observation."""

    if new_count <= 0:
        raise ValueError("new_count must be positive")
    return previous_mean + (observation - previous_mean) / new_count


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
