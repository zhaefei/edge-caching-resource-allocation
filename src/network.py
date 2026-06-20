"""Wireless edge network generation and rate calculation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import SimulationConfig


@dataclass(frozen=True)
class NetworkState:
    """Geometry, associations, and channel gains for one simulation run."""

    user_positions: np.ndarray
    server_positions: np.ndarray
    associations: np.ndarray
    channel_gains: np.ndarray


def generate_network(config: SimulationConfig, rng: np.random.Generator) -> NetworkState:
    """Generate users, edge servers, nearest-server associations, and channels."""

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
    channel_gains = compute_channel_gains(user_positions, server_positions, config)

    return NetworkState(
        user_positions=user_positions,
        server_positions=server_positions,
        associations=associations,
        channel_gains=channel_gains,
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

    distances = np.linalg.norm(
        user_positions[:, None, :] - server_positions[None, :, :],
        axis=2,
    )
    distances = np.maximum(distances, config.min_distance_m)
    gains = config.reference_gain / (distances**config.path_loss_exponent)
    return gains


def compute_user_rates_mbps(
    config: SimulationConfig,
    network: NetworkState,
    user_bandwidth_hz: np.ndarray,
) -> np.ndarray:
    """Compute each user's downlink rate with the Shannon capacity formula.

    Rate model:
        R_u = B_u log2(1 + SINR_u)

    Interference is simplified as a fraction of received power from
    non-associated edge servers.
    """

    num_users = network.user_positions.shape[0]
    rates = np.zeros(num_users, dtype=float)
    noise_figure_linear = 10 ** (config.noise_figure_db / 10.0)

    for user_id in range(num_users):
        server_id = int(network.associations[user_id])
        bandwidth = max(float(user_bandwidth_hz[user_id]), 1.0)

        desired_gain = network.channel_gains[user_id, server_id]
        signal_power = config.tx_power_watt * desired_gain

        all_received_powers = config.tx_power_watt * network.channel_gains[user_id]
        interference_power = config.interference_factor * (
            np.sum(all_received_powers) - signal_power
        )
        noise_power = config.noise_density_w_per_hz * bandwidth * noise_figure_linear
        sinr = signal_power / max(noise_power + interference_power, 1e-30)

        rates[user_id] = bandwidth * np.log2(1.0 + sinr) / 1e6

    return rates
