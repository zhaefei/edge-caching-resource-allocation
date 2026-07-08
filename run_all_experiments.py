"""Run the default simulation and all experiment sweeps."""

from config import SimulationConfig
from main import main as run_main
from experiments.run_backhaul_sensitivity_experiment import (
    main as run_backhaul_sensitivity,
)
from experiments.run_bandwidth_sensitivity_experiment import (
    main as run_bandwidth_sensitivity,
)
from experiments.run_cache_capacity_experiment import main as run_cache_capacity
from experiments.run_file_size_variability_experiment import (
    main as run_file_size_variability,
)
from experiments.run_multi_seed_cache_capacity_experiment import (
    main as run_multi_seed_cache_capacity,
)
from experiments.run_spatial_locality_experiment import (
    main as run_spatial_locality,
)
from experiments.run_user_activity_experiment import main as run_user_activity
from experiments.run_user_density_experiment import main as run_user_density
from experiments.run_zipf_experiment import main as run_zipf
from generate_report_assets import main as generate_report_assets
from summarize_results import main as summarize_results
from src.reproducibility import write_run_metadata


def main() -> None:
    run_main()
    run_cache_capacity()
    run_file_size_variability()
    run_user_density()
    run_user_activity()
    run_zipf()
    run_spatial_locality()
    run_backhaul_sensitivity()
    run_bandwidth_sensitivity()
    run_multi_seed_cache_capacity()
    summarize_results()
    generate_report_assets()
    config = SimulationConfig()
    write_run_metadata(
        config,
        config.results_dir / "data" / "all_experiments_metadata.json",
        run_name="all_experiments",
    )
    print("\nAll experiments completed.")


if __name__ == "__main__":
    main()
