import os
import pandas as pd

# Hardcoded paths for configuration
MATCH_CONTEXT_CSV = "/home/ds/Desktop/ten/data/processed/match_context.csv"
SIM_READY_CSV = "/home/ds/Desktop/ten/data/processed/sim_ready.csv"
LOGS_DIR = "/home/ds/Desktop/ten/logs"
ATP_CSV = "/home/ds/Desktop/ten/data/raw/atp.csv"
WTA_CSV = "/home/ds/Desktop/ten/data/raw/wta.csv"

from data_preparation import run_data_preparation
from name_resolution import run_name_resolution
from stats_integration import run_stats_integration

import logging

def setup_logger(name):
    """Setup and return a logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger("sim_prep_main")

def save_dataframe(df, path, description):
    """Save a DataFrame to CSV and log the operation."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        logger.info(f"{description} saved successfully to {path}.")
    except Exception as e:
        logger.error(f"Failed to save {description} to {path}: {e}")
        raise

def run_sim_prep(sourced_strength=0.1, estimated_strength=0.1):
    """
    Orchestrate the simulation preparation process, including:
    - Data preparation
    - Name resolution
    - Stats integration

    Returns:
        pd.DataFrame: The final simulation-ready DataFrame.
    """
    try:
        # Step 1: Data Preparation
        logger.info("Starting data preparation...")
        match_context, combined_stats = run_data_preparation(MATCH_CONTEXT_CSV, ATP_CSV, WTA_CSV)
        logger.info("Data preparation completed.")

        # Step 2: Name Resolution
        logger.info("Starting name resolution...")
        resolved_context = run_name_resolution(match_context, combined_stats, SIM_READY_CSV, LOGS_DIR)
        logger.info("Name resolution completed.")

        # Step 3: Stats Integration
        logger.info("Starting stats integration...")
        sim_ready_df = run_stats_integration(
            resolved_context,
            combined_stats,
            SIM_READY_CSV,
            sourced_strength=sourced_strength,
            estimated_strength=estimated_strength,
        )
        logger.info("Stats integration completed.")

        # Save simulation-ready data
        save_dataframe(sim_ready_df, SIM_READY_CSV, "Simulation-ready data")

        logger.info("Simulation preparation pipeline completed successfully.")
        return sim_ready_df

    except Exception as e:
        logger.error(f"Error during simulation preparation: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting simulation preparation pipeline...")
    sim_ready_df = run_sim_prep()
    logger.info("Pipeline completed. Simulation-ready data is available.")
