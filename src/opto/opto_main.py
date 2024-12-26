import logging
from opto_data_prep import run_opto_data_prep
from builder import run_builder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# File paths
PLAYER_POOL_PATH = "data/raw/pool.csv"
SIMULATION_DETAILS_PATH = "data/processed/simulation_details.csv"
SIM_PREPPED_PATH = "data/processed/sim_prepped.csv"

# Settings adjustable by user
BUCKET_SIZE = 15  # Number of simulations to average per projection set
NUM_LINEUPS = 20  # Number of projection sets to generate
SALARY_CAP = 50000  # Salary cap for each lineup
ROSTER_SIZE = 6  # Number of players per lineup


def main():
    """
    Main function to orchestrate the optimizer workflow.
    """
    logging.info("Starting optimizer workflow...")

    try:
        # Step 1: Data Preparation
        projection_sets, usage_summary = run_opto_data_prep(
            PLAYER_POOL_PATH, SIMULATION_DETAILS_PATH, SIM_PREPPED_PATH, BUCKET_SIZE, NUM_LINEUPS
        )

        if not projection_sets:
            logging.error("Failed to prepare projection sets. Exiting.")
            return

        # Log usage summary
        for summary in usage_summary:
            logging.info(summary)

        # Step 2: Lineup Builder
        final_lineups = run_builder(projection_sets, SALARY_CAP, ROSTER_SIZE, NUM_LINEUPS)

        if not final_lineups.empty:
            logging.info("Optimization workflow completed successfully.")
            logging.info("\nFinal Lineups:\n")
            logging.info(final_lineups.to_string(index=False))
        else:
            logging.warning("No lineups were built.")

    except Exception as e:
        logging.error(f"An error occurred during the optimizer workflow: {e}")


if __name__ == "__main__":
    main()
