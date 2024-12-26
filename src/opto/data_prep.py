#opto_data_prep


import pandas as pd
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_player_pool(player_pool_path):
    """Loads the player pool with salaries from a CSV file."""
    try:
        player_pool = pd.read_csv(player_pool_path)
        logging.info(f"Loaded {len(player_pool)} rows from {player_pool_path}")
        return player_pool
    except Exception as e:
        logging.error(f"Error loading player pool: {e}")
        return pd.DataFrame()


def load_simulation_details(simulation_details_path):
    """Loads the simulation details from a CSV file."""
    try:
        simulation_details = pd.read_csv(simulation_details_path)
        logging.info(f"Loaded {len(simulation_details)} rows from {simulation_details_path}")
        return simulation_details
    except Exception as e:
        logging.error(f"Error loading simulation details: {e}")
        return pd.DataFrame()


def load_sim_prepped(sim_prepped_path):
    """Loads the sim_prepped file to retrieve MatchIDs."""
    try:
        sim_prepped = pd.read_csv(sim_prepped_path)
        logging.info(f"Loaded {len(sim_prepped)} rows from {sim_prepped_path}")
        return sim_prepped
    except Exception as e:
        logging.error(f"Error loading sim_prepped file: {e}")
        return pd.DataFrame()


def prepare_projection_sets(player_pool, simulation_details, sim_prepped, bucket_size, num_lineups):
    """Prepares multiple projection sets for optimization with MatchID."""
    projection_sets = []
    usage_summary = []

    # Merge MatchID from sim_prepped with simulation details
    simulation_details_with_ids = pd.merge(
        simulation_details.transpose().reset_index(),
        sim_prepped[['MatchID', 'Player']],
        left_on='index',
        right_on='Player',
        how='left'
    )
    simulation_details_with_ids.drop(columns='index', inplace=True)

    for i in range(num_lineups):
        # Select random simulations for the bucket
        selected_indices = random.sample(range(len(simulation_details)), bucket_size)
        averaged_projection = simulation_details.iloc[selected_indices].mean().to_frame().T

        # Reshape the DataFrame
        reshaped_data = averaged_projection.transpose().reset_index()
        reshaped_data.columns = ['Player', 'Projection']

        # Merge with player pool to add salary
        player_pool = player_pool.rename(columns={"Name": "Player"})
        merged_data = reshaped_data.merge(player_pool[['Player', 'Salary']], on='Player', how='left')

        # Merge with MatchID
        merged_data = pd.merge(
            merged_data,
            sim_prepped[['MatchID', 'Player']],
            on='Player',
            how='left'
        )

        # Ensure the projection set has the correct column names
        projection_set = merged_data[['Player', 'Salary', 'MatchID', 'Projection']]
        projection_sets.append(projection_set)

        # Log simulation indices used for this projection set
        usage_summary.append(f"Projection Set {i + 1} - Slate Sims: {', '.join(map(str, selected_indices))}")

    return projection_sets, usage_summary


def run_opto_data_prep(player_pool_path, simulation_details_path, sim_prepped_path, bucket_size, num_lineups):
    """Wrapper function for optimizer data preparation."""
    logging.info("Starting optimizer data preparation...")
    player_pool = load_player_pool(player_pool_path)
    simulation_details = load_simulation_details(simulation_details_path)
    sim_prepped = load_sim_prepped(sim_prepped_path)

    if player_pool.empty or simulation_details.empty or sim_prepped.empty:
        logging.error("Failed to load necessary data files. Exiting.")
        return [], []

    projection_sets, usage_summary = prepare_projection_sets(
        player_pool, simulation_details, sim_prepped, bucket_size, num_lineups
    )

    logging.info("Data preparation completed successfully.")
    for summary in usage_summary:
     return projection_sets, usage_summary


if __name__ == "__main__":
    logging.info("This script is designed to be imported, not run directly.")
