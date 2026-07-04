"""Content request generation for wireless edge caching simulations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from config import SimulationConfig

if TYPE_CHECKING:
    from src.network import NetworkState


@dataclass(frozen=True)
class RequestTrace:
    """A sequence of user requests for content files."""

    user_ids: np.ndarray
    file_ids: np.ndarray
    file_sizes_mbits: np.ndarray
    popularity: np.ndarray
    user_activity: np.ndarray
    server_popularity: np.ndarray | None = None


def zipf_probabilities(num_items: int, alpha: float) -> np.ndarray:
    """Return Zipf probabilities for item ranks 1, ..., N."""

    if alpha <= 0:
        return np.ones(num_items, dtype=float) / num_items

    ranks = np.arange(1, num_items + 1, dtype=float)
    weights = 1.0 / (ranks**alpha)
    return weights / np.sum(weights)


def generate_request_trace(
    config: SimulationConfig,
    rng: np.random.Generator,
    network: "NetworkState | None" = None,
) -> RequestTrace:
    """Generate a reproducible request trace.

    Content files follow a Zipf distribution, which is commonly used to model
    skewed video or web object popularity. User activity is mildly skewed so
    that demand-aware bandwidth allocation has a clear interpretation.
    """

    popularity = zipf_probabilities(config.num_files, config.zipf_alpha)
    user_activity = zipf_probabilities(config.num_users, config.user_activity_alpha)
    server_popularity = build_server_popularity_profiles(config, popularity)
    file_sizes_mbits = generate_file_size_profile(config, rng)

    user_ids = rng.choice(
        config.num_users,
        size=config.num_requests,
        p=user_activity,
    )
    file_ids = _sample_requested_files(
        config,
        rng,
        user_ids,
        popularity,
        server_popularity,
        network,
    )

    return RequestTrace(
        user_ids=user_ids,
        file_ids=file_ids,
        file_sizes_mbits=file_sizes_mbits,
        popularity=popularity,
        user_activity=user_activity,
        server_popularity=server_popularity if network is not None else None,
    )


def generate_file_size_profile(
    config: SimulationConfig,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate a lightweight heterogeneous file-size profile."""

    if config.file_size_sigma <= 0.0:
        return np.full(config.num_files, config.file_size_mbits, dtype=float)

    sizes = rng.lognormal(
        mean=np.log(config.file_size_mbits),
        sigma=config.file_size_sigma,
        size=config.num_files,
    )
    sizes *= config.file_size_mbits / float(np.mean(sizes))
    return np.clip(
        sizes,
        config.min_file_size_mbits,
        config.max_file_size_mbits,
    )


def build_server_popularity_profiles(
    config: SimulationConfig,
    global_popularity: np.ndarray,
) -> np.ndarray:
    """Create mild server-specific popularity profiles from the global Zipf law."""

    profiles = np.tile(global_popularity, (config.num_edge_servers, 1))

    if config.spatial_locality_strength <= 0.0 or config.num_edge_servers <= 1:
        return profiles

    file_groups = np.array_split(np.arange(config.num_files), config.num_edge_servers)

    for server_id, preferred_files in enumerate(file_groups):
        boosted = global_popularity.copy()
        boosted[preferred_files] *= config.local_preference_boost
        boosted /= np.sum(boosted)
        profiles[server_id] = (
            (1.0 - config.spatial_locality_strength) * global_popularity
            + config.spatial_locality_strength * boosted
        )
        profiles[server_id] /= np.sum(profiles[server_id])

    return profiles


def _sample_requested_files(
    config: SimulationConfig,
    rng: np.random.Generator,
    user_ids: np.ndarray,
    global_popularity: np.ndarray,
    server_popularity: np.ndarray,
    network: "NetworkState | None",
) -> np.ndarray:
    """Sample file requests with optional server-dependent content preferences."""

    if network is None or config.spatial_locality_strength <= 0.0:
        return rng.choice(
            config.num_files,
            size=config.num_requests,
            p=global_popularity,
        )

    request_servers = network.associations[user_ids]
    file_ids = np.empty(config.num_requests, dtype=int)

    for server_id in range(config.num_edge_servers):
        request_mask = request_servers == server_id
        request_count = int(np.sum(request_mask))
        if request_count == 0:
            continue

        file_ids[request_mask] = rng.choice(
            config.num_files,
            size=request_count,
            p=server_popularity[server_id],
        )

    return file_ids


def file_request_counts(file_ids: np.ndarray, num_files: int) -> np.ndarray:
    """Count how many times each file appears in a request trace."""

    return np.bincount(file_ids, minlength=num_files)


def user_request_counts(user_ids: np.ndarray, num_users: int) -> np.ndarray:
    """Count how many requests are generated by each user."""

    return np.bincount(user_ids, minlength=num_users)
