import pandas as pd
import logging
from pulp import LpProblem, LpVariable, LpMaximize, lpSum, LpBinary, LpStatus
from src.opto.opto_data_prep import prepare_simulation_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
SALARY_CAP = 50000
ROSTER_SIZE = 6


def optimize_lineup(prepared_data):
    """
    Optimize DFS lineup based on projected scores and salary cap.

    Args:
        prepared_data (pd.DataFrame): DataFrame containing player data with projected scores and salaries.
            Expected columns: 'Player', 'Salary', 'Score'.

    Returns:
        pd.DataFrame: DataFrame of selected players for the lineup.
    """
    # Validate required columns
    required_columns = {'Player', 'Salary', 'Score'}
    if not required_columns.issubset(prepared_data.columns):
        raise ValueError(f"Prepared data must contain columns: {required_columns}")

    # Create the LP problem
    prob = LpProblem("Lineup Optimization", LpMaximize)

    # Create decision variables
    player_vars = LpVariable.dicts("Player", prepared_data.index, cat=LpBinary)

    # Objective function: Maximize total projected score
    prob += lpSum([prepared_data.loc[i, 'Score'] * player_vars[i] for i in prepared_data.index])

    # Constraint: Total salary must be less than or equal to the salary cap
    prob += lpSum([prepared_data.loc[i, 'Salary'] * player_vars[i] for i in prepared_data.index]) <= SALARY_CAP

    # Constraint: Roster size (e.g., select 6 players)
    prob += lpSum([player_vars[i] for i in prepared_data.index]) == ROSTER_SIZE

    # Solve the problem
    prob.solve()

    # Log optimizer status
    logging.info(f"Optimizer Status: {LpStatus[prob.status]}")

    # Check if a valid solution was found
    if prob.status != 1:
        logging.warning("No optimal solution found for the lineup optimization.")
        return pd.DataFrame()

    # Get the selected players
    selected_indices = [i for i in prepared_data.index if player_vars[i].varValue == 1]
    selected_players = prepared_data.loc[selected_indices].reset_index(drop=True)

    return selected_players


def build_lineups(prepared_data, bucket_size, num_lineups):
    """
    Build multiple lineups based on specified diversity (bucket size).

    Args:
        prepared_data (pd.DataFrame): Prepared simulation data.
        bucket_size (int): Number of buckets for simulation diversity.
        num_lineups (int): Number of lineups to generate.

    Returns:
        pd.DataFrame: DataFrame containing generated lineups.
    """
    lineups = []

    for lineup_index in range(num_lineups):
        # Determine the bucket for this lineup
        if bucket_size == 1:
            # Low diversity: Use average scores from all simulations
            bucket_data = prepared_data.copy()
        else:
            # High diversity: Use scores from a single random simulation
            bucket_column = f"Simulation_{lineup_index % bucket_size + 1}"
            if bucket_column not in prepared_data.columns:
                logging.warning(f"Bucket column {bucket_column} not found. Skipping this lineup.")
                continue

            bucket_data = prepared_data[['Player', 'Salary', bucket_column]].rename(columns={bucket_column: 'Score'})

        # Optimize lineup
        optimized_lineup = optimize_lineup(bucket_data)
        if optimized_lineup.empty:
            logging.warning(f"Lineup {lineup_index + 1} could not be built. Skipping.")
            continue

        # Add lineup to results
        lineup_entry = {
            f"Player_{i + 1}": optimized_lineup.iloc[i]['Player'] if i < len(optimized_lineup) else None
            for i in range(ROSTER_SIZE)
        }
        lineup_entry["Total_Score"] = optimized_lineup['Score'].sum()
        lineup_entry["Total_Salary"] = optimized_lineup['Salary'].sum()
        lineups.append(lineup_entry)

    # Convert to DataFrame
    return pd.DataFrame(lineups)


def run_optimizer_pipeline(simulation_details_path, player_pool_path, bucket_size, num_lineups):
    """
    Orchestrates the optimization pipeline.

    Args:
        simulation_details_path (str): Path to the simulation details CSV.
        player_pool_path (str): Path to the player pool CSV.
        bucket_size (int): Number of buckets for simulation diversity.
        num_lineups (int): Number of lineups to generate.

    Returns:
        pd.DataFrame: DataFrame containing generated lineups.
    """
    # Load and prepare data
    logging.info("Loading and preparing data...")
    player_pool = pd.read_csv(player_pool_path)
    simulation_details = pd.read_csv(simulation_details_path)

    prepared_data = prepare_simulation_data(simulation_details, player_pool)

    # Build lineups
    logging.info("Building lineups...")
    lineups = build_lineups(prepared_data, bucket_size, num_lineups)

    return lineups


def main():
    """
    Main function for the optimizer script.
    """
    # File paths
    simulation_details_path = "data/processed/simulation_details.csv"
    player_pool_path = "data/raw/pool.csv"
    output_path = "data/processed/optimized_lineups.csv"

    # Parameters
    bucket_size = 10
    num_lineups = 50

    # Run the optimizer pipeline
    try:
        lineups = run_optimizer_pipeline(simulation_details_path, player_pool_path, bucket_size, num_lineups)
        
        if not lineups.empty:
            # Save the results
            lineups.to_csv(output_path, index=False)
            logging.info(f"Optimized lineups saved to {output_path}.")
        else:
            logging.warning("No lineups were successfully generated.")

    except Exception as e:
        logging.error(f"Error during optimization: {e}")


if __name__ == "__main__":
    main()
