from src.sim.sim_prep.data_preparation import run_data_preparation
from src.sim.sim_prep.name_resolution import run_name_resolution
from src.sim.sim_prep.stats_integration import run_stats_integration
from src.utils.logger import setup_logger
import pandas as pd

logger = setup_logger("sim_prep_main")

def run_sim_prep(sourced_strength=0.1, estimated_strength=0.1):
    """
    Orchestrate the entire simulation preparation process.
    """
    try:
        logger.info("Starting data preparation...")
        match_context, combined_stats = run_data_preparation()

        logger.info("Starting name resolution...")
        resolved_context = run_name_resolution(match_context, combined_stats)

        if not isinstance(resolved_context, pd.DataFrame):
            raise TypeError("Name resolution output is not of type DataFrame.")
        logger.info(f"Name resolution complete. Resolved context has {len(resolved_context)} rows.")

        logger.info("Starting stats integration...")
        sim_ready_df = run_stats_integration(
            resolved_context,
            combined_stats,
            sourced_strength=sourced_strength,
            estimated_strength=estimated_strength
        )

        logger.info("Simulation preparation completed successfully.")
        return sim_ready_df
    except Exception as e:
        logger.error(f"Error during simulation preparation: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting simulation preparation...")
    sim_ready_df = run_sim_prep()
    logger.info("Simulation-ready data created!")
