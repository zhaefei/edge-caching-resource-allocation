"""Configuration for the edge caching simulation project."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SimulationConfig:
    """Default parameters for a reproducible wireless edge simulation.

    The values are intentionally simple and undergraduate-friendly. They are
    not meant to reproduce a specific 3GPP scenario, but they preserve the
    physical meaning of wireless rate, cache capacity, and backhaul delay.
    """

    seed: int = 42

    # Network scale
    num_files: int = 50
    num_users: int = 100
    num_edge_servers: int = 4
    cache_capacity: int = 8
    area_size_m: float = 500.0

    # Request model
    num_requests: int = 5000
    zipf_alpha: float = 0.9
    user_activity_alpha: float = 0.4
    spatial_locality_strength: float = 0.35
    local_preference_boost: float = 3.0

    # Wireless channel and resource model
    bandwidth_hz: float = 20e6  # total downlink bandwidth per edge server
    tx_power_watt: float = 0.2
    noise_density_w_per_hz: float = 10 ** ((-174.0 - 30.0) / 10.0)
    noise_figure_db: float = 7.0
    interference_factor: float = 0.15
    reference_gain: float = 1e-3
    path_loss_exponent: float = 3.4
    min_distance_m: float = 1.0

    # Content and backhaul model. A file is interpreted as a video/data chunk.
    file_size_mbits: float = 5.0
    backhaul_latency_ms: float = 80.0
    backhaul_rate_mbps: float = 100.0

    # Output
    results_dir: Path = Path("results")
