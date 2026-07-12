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


class PathLossChannelModel(WirelessChannelModel):
    """Large-scale distance path-loss channel model."""

    name = "path_loss"

    def compute_channel_gains(
        self,
        user_positions: np.ndarray,
        server_positions: np.ndarray,
        config: SimulationConfig,
    ) -> np.ndarray:
        return self._compute_path_loss_gains(
            user_positions,
            server_positions,
            config,
        )

    def _compute_path_loss_gains(
        self,
        user_positions: np.ndarray,
        server_positions: np.ndarray,
        config: SimulationConfig,
    ) -> np.ndarray:
        """Compute deterministic large-scale path-loss gains."""

        if (
            config.path_loss_reference_distance_m <= 0.0
            or config.path_loss_reference_gain <= 0.0
            or config.path_loss_exponent <= 0.0
            or config.min_distance_m <= 0.0
        ):
            raise ValueError(
                "Path-loss reference distance, reference gain, exponent, and "
                "minimum distance must all be positive."
            )

        distances = np.linalg.norm(
            user_positions[:, None, :] - server_positions[None, :, :],
            axis=2,
        )
        distances = np.maximum(distances, config.min_distance_m)
        return config.path_loss_reference_gain * (
            config.path_loss_reference_distance_m / distances
        ) ** config.path_loss_exponent

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


class BaselineDistanceChannelModel(PathLossChannelModel):
    """Backward-compatible alias for the original distance-based baseline."""

    name = "baseline_distance"


class PathLossWithFadingChannelModel(PathLossChannelModel):
    """Path-loss model with lightweight bounded fading per user-server link."""

    name = "path_loss_fading"

    def compute_channel_gains(
        self,
        user_positions: np.ndarray,
        server_positions: np.ndarray,
        config: SimulationConfig,
    ) -> np.ndarray:
        if (
            config.fading_min_power_gain <= 0.0
            or config.fading_max_power_gain < config.fading_min_power_gain
        ):
            raise ValueError(
                "Fading bounds must satisfy 0 < fading_min_power_gain <= "
                "fading_max_power_gain."
            )

        path_loss_gains = self._compute_path_loss_gains(
            user_positions,
            server_positions,
            config,
        )
        rng = np.random.default_rng(config.seed + config.fading_seed_offset)
        # Exponential power gain is the squared-amplitude form of Rayleigh fading.
        fading_power_gains = rng.exponential(scale=1.0, size=path_loss_gains.shape)
        fading_power_gains = np.clip(
            fading_power_gains,
            config.fading_min_power_gain,
            config.fading_max_power_gain,
        )
        return path_loss_gains * fading_power_gains


def resolve_wireless_channel_model(
    config: SimulationConfig,
) -> WirelessChannelModel:
    """Return the configured wireless channel model."""

    if config.wireless_channel_model == PathLossChannelModel.name:
        return PathLossChannelModel()

    if config.wireless_channel_model == BaselineDistanceChannelModel.name:
        return BaselineDistanceChannelModel()

    if config.wireless_channel_model == PathLossWithFadingChannelModel.name:
        return PathLossWithFadingChannelModel()

    raise ValueError(
        f"Unsupported wireless channel model: {config.wireless_channel_model}"
    )
