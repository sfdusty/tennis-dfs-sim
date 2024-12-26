import logging
from data_prep import run_opto_data_prep
from builder import run_builder
from utils import display_optimal_lineup, display_player_exposure, lineup_summary, select_valid_lineups
from config import *

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        large_pool_size = NUM_LINEUPS * LARGER_POOL_MULTIPLE
        lineup_pool = run_builder(projection_sets, SALARY_CAP, ROSTER_SIZE, large_pool_size)

        # Step 3: Select Valid Lineups
        final_lineups = select_valid_lineups(lineup_pool, NUM_LINEUPS, UNIQUE_PLAYERS_BETWEEN_LINEUPS)

        # Step 4: Display Summaries
        lineup_summary(lineup_pool, final_lineups)

        if not final_lineups.empty:
            logging.info("Optimization workflow completed successfully.")

            # Display optimal lineups
            display_optimal_lineup(final_lineups)

            # Display player exposure
            display_player_exposure(lineup_pool, final_lineups)
        else:
            logging.warning("No valid lineups were built.")

    except Exception as e:
        logging.error(f"An error occurred during the optimizer workflow: {e}")

if __name__ == "__main__":
    main()
