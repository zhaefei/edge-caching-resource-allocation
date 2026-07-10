"""Wireless edge network generation and rate calculation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import SimulationConfig
from src.wireless_channel import resolve_wireless_channel_model


@dataclass(frozen=True)
class NetworkState:
    """Geometry, associations, and channel gains for one simulation run."""

    user_positions: np.ndarray
    server_positions: np.ndarray
    associations: np.ndarray
    channel_gains: np.ndarray
    channel_model_name: str


def generate_network(config: SimulationConfig, rng: np.random.Generator) -> NetworkState:
    """Generate users, edge servers, nearest-server associations, and channels."""

    channel_model = resolve_wireless_channel_model(config)
    server_positions = _place_edge_servers_on_grid(
        config.num_edge_servers,
        config.area_size_m,
    )
    user_positions = rng.uniform(
        low=0.0,
        high=config.area_size_m,
        size=(config.num_users, 2),
    )
    associations = associate_users_to_nearest_server(user_positions, server_positions)
    channel_gains = channel_model.compute_channel_gains(
        user_positions,
        server_positions,
        config,
    )

    return NetworkState(
        user_positions=user_positions,
        server_positions=server_positions,
        associations=associations,
        channel_gains=channel_gains,
        channel_model_name=channel_model.name,
    )


def _place_edge_servers_on_grid(num_servers: int, area_size_m: float) -> np.ndarray:
    """Place edge servers on a simple grid to cover the square service area."""

    grid_size = int(np.ceil(np.sqrt(num_servers)))
    coordinates = np.linspace(0.2 * area_size_m, 0.8 * area_size_m, grid_size)
    mesh_x, mesh_y = np.meshgrid(coordinates, coordinates)
    positions = np.column_stack([mesh_x.ravel(), mesh_y.ravel()])
    return positions[:num_servers]


def associate_users_to_nearest_server(
    user_positions: np.ndarray,
    server_positions: np.ndarray,
) -> np.ndarray:
    """Associate each user with the nearest edge server."""

    distances = np.linalg.norm(
        user_positions[:, None, :] - server_positions[None, :, :],
        axis=2,
    )
    return np.argmin(distances, axis=1)


def compute_channel_gains(
    user_positions: np.ndarray,
    server_positions: np.ndarray,
    config: SimulationConfig,
) -> np.ndarray:
    """Compute large-scale channel gains with a distance path-loss model."""

    channel_model = resolve_wireless_channel_model(config)
    return channel_model.compute_channel_gains(
        user_positions,
        server_positions,
        config,
    )


def compute_user_rates_mbps(
    config: SimulationConfig,
    network: NetworkState,
    user_bandwidth_hz: np.ndarray,
) -> np.ndarray:
    """Compute each user's downlink rate with the configured channel model."""

    channel_model = resolve_wireless_channel_model(config)
    return channel_model.compute_user_rates_mbps(
        config,
        network.channel_gains,
        network.associations,
        user_bandwidth_hz,
    )
