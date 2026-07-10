"""Wireless channel model abstractions used by the simulator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from config import SimulationConfig


@dataclass(frozen=True)
class ChannelComputation:
    """Intermediate wireless quantities for one simulation snapshot."""

    channel_gains: np.ndarray
    signal_powers_w: np.ndarray
    interference_powers_w: np.ndarray
    noise_powers_w: np.ndarray
    sinr_linear: np.ndarray


class WirelessChannelModel(ABC):
    """Small interface for pluggable channel and rate calculations."""

    name: str

    @abstractmethod
    def compute_channel_gains(
        self,
        user_positions: np.ndarray,
        server_positions: np.ndarray,
        config: SimulationConfig,
    ) -> np.ndarray:
        """Return per-user per-server large-scale channel gains."""

    @abstractmethod
    def compute_channel_metrics(
        self,
        config: SimulationConfig,
        channel_gains: np.ndarray,
        associations: np.ndarray,
        user_bandwidth_hz: np.ndarray,
    ) -> ChannelComputation:
        """Return SINR ingredients for the current associations."""

    def compute_user_rates_mbps(
        self,
        config: SimulationConfig,
        channel_gains: np.ndarray,
        associations: np.ndarray,
        user_bandwidth_hz: np.ndarray,
    ) -> np.ndarray:
        """Convert channel metrics into downlink rates in Mbit/s."""

        metrics = self.compute_channel_metrics(
            config,
            channel_gains,
            associations,
            user_bandwidth_hz,
        )
        bandwidth = np.maximum(np.asarray(user_bandwidth_hz, dtype=float), 1.0)
        return bandwidth * np.log2(1.0 + metrics.sinr_linear) / 1e6


class BaselineDistanceChannelModel(WirelessChannelModel):
    """Current large-scale distance model used as the default baseline."""

    name = "baseline_distance"

    def compute_channel_gains(
        self,
        user_positions: np.ndarray,
        server_positions: np.ndarray,
        config: SimulationConfig,
    ) -> np.ndarray:
        distances = np.linalg.norm(
            user_positions[:, None, :] - server_positions[None, :, :],
            axis=2,
        )
        distances = np.maximum(distances, config.min_distance_m)
        return config.reference_gain / (distances**config.path_loss_exponent)

    def compute_channel_metrics(
        self,
        config: SimulationConfig,
        channel_gains: np.ndarray,
        associations: np.ndarray,
        user_bandwidth_hz: np.ndarray,
    ) -> ChannelComputation:
        bandwidth = np.maximum(np.asarray(user_bandwidth_hz, dtype=float), 1.0)
        user_index = np.arange(len(associations), dtype=int)
        serving_gains = channel_gains[user_index, associations]
        signal_powers_w = config.tx_power_watt * serving_gains
        all_received_powers = config.tx_power_watt * channel_gains
        interference_powers_w = config.interference_factor * (
            np.sum(all_received_powers, axis=1) - signal_powers_w
        )
        noise_figure_linear = 10 ** (config.noise_figure_db / 10.0)
        noise_powers_w = (
            config.noise_density_w_per_hz * bandwidth * noise_figure_linear
        )
        sinr_linear = signal_powers_w / np.maximum(
            noise_powers_w + interference_powers_w,
            1e-30,
        )

        return ChannelComputation(
            channel_gains=channel_gains,
            signal_powers_w=signal_powers_w,
            interference_powers_w=interference_powers_w,
            noise_powers_w=noise_powers_w,
            sinr_linear=sinr_linear,
        )


def resolve_wireless_channel_model(
    config: SimulationConfig,
) -> WirelessChannelModel:
    """Return the configured wireless channel model."""

    if config.wireless_channel_model == BaselineDistanceChannelModel.name:
        return BaselineDistanceChannelModel()

    raise ValueError(
        f"Unsupported wireless channel model: {config.wireless_channel_model}"
    )
