"""Run the default simulation and all experiment sweeps."""

from main import main as run_main
from experiments.run_cache_capacity_experiment import main as run_cache_capacity
from experiments.run_multi_seed_cache_capacity_experiment import (
    main as run_multi_seed_cache_capacity,
)
from experiments.run_user_density_experiment import main as run_user_density
from experiments.run_zipf_experiment import main as run_zipf
from generate_report_assets import main as generate_report_assets
from summarize_results import main as summarize_results


def main() -> None:
    run_main()
    run_cache_capacity()
    run_user_density()
    run_zipf()
    run_multi_seed_cache_capacity()
    summarize_results()
    generate_report_assets()
    print("\nAll experiments completed.")


if __name__ == "__main__":
    main()
