import logging
import pandas as pd

# ============================
# Lineup Display Functions
# ============================
def display_optimal_lineup(lineups):
    """
    Displays each optimal lineup grouped by LineupID with total projection and salary.

    Args:
        lineups (pd.DataFrame): The DataFrame of selected lineups, including a LineupID column.
    """
    if lineups.empty:
        logging.warning("No lineups to display.")
        return

    grouped_lineups = lineups.groupby('LineupID')

    for lineup_id, group in grouped_lineups:
        logging.info(f"\nOptimal Lineup #{lineup_id}:\n")
        print(group[['Player', 'MatchID', 'Projection', 'Salary']])

        total_projection = group['Projection'].sum()
        total_salary = group['Salary'].sum()

        logging.info(f"Total Projection: {total_projection}")
        logging.info(f"Total Salary: {total_salary}")


def display_player_exposure(lineup_pool, selected_lineups):
    """
    Displays player exposure in the larger pool and the selected lineup set.

    Args:
        lineup_pool (pd.DataFrame): The full pool of lineups.
        selected_lineups (pd.DataFrame): The selected valid lineups.
    """
    if lineup_pool.empty or selected_lineups.empty:
        logging.warning("Cannot calculate exposure. One or both DataFrames are empty.")
        return

    # Calculate exposure in the larger pool
    pool_exposure = lineup_pool['Player'].value_counts()

    # Calculate exposure in the selected lineup set
    lineup_exposure = selected_lineups['Player'].value_counts()

    # Merge into a single DataFrame
    exposure_df = pd.DataFrame({
        "Player": pool_exposure.index,
        "Larger Pool Exposure": pool_exposure.values,
        "Lineup Set Exposure": lineup_exposure.reindex(pool_exposure.index, fill_value=0).values
    })

    # Sort by lineup set exposure, descending
    exposure_df = exposure_df.sort_values(by="Lineup Set Exposure", ascending=False)

    logging.info("\nPlayer Exposure:\n")
    print(exposure_df.to_string(index=False))


# ============================
# Lineup Selection Functions
# ============================
def select_valid_lineups(lineup_pool, num_lineups, unique_players_between_lineups):
    """
    Selects the highest-scoring valid lineups from a pool.

    Returns:
        pd.DataFrame: The selected valid lineups.
    """
    valid_lineups = []
    selected_players = set()

    # Group by LineupID and sort by total projection
    grouped_lineups = lineup_pool.groupby("LineupID").agg(
        TotalProjection=("Projection", "sum"),
        TotalSalary=("Salary", "sum")
    ).sort_values(by="TotalProjection", ascending=False)

    for lineup_id, _ in grouped_lineups.iterrows():
        lineup = lineup_pool[lineup_pool["LineupID"] == lineup_id]

        # Ensure no duplicate match IDs in the lineup
        if len(lineup["MatchID"]) > len(lineup["MatchID"].drop_duplicates()):
            continue

        # Check for unique players between lineups
        lineup_players = set(lineup["Player"])
        if len(selected_players.intersection(lineup_players)) < len(lineup_players) - unique_players_between_lineups:
            valid_lineups.append(lineup)
            selected_players.update(lineup_players)

        if len(valid_lineups) >= num_lineups:
            break

    if valid_lineups:
        return pd.concat(valid_lineups, ignore_index=True)
    else:
        return pd.DataFrame()


# ============================
# Lineup Summary Functions
# ============================
def lineup_summary(lineup_pool, selected_lineups):
    """
    Displays high-level summaries of the lineup pool and selected lineups.

    Args:
        lineup_pool (pd.DataFrame): The full pool of lineups with LineupID.
        selected_lineups (pd.DataFrame): The selected valid lineups.
    """
    if lineup_pool.empty:
        logging.warning("Lineup pool is empty. Cannot compute summary.")
        return

    # Identify duplicate lineups in the pool
    lineup_hashes = lineup_pool.groupby("LineupID")["Player"].apply(tuple)
    duplicate_count = lineup_hashes.duplicated(keep=False).sum()

    # Identify lineups with players from the same match
    def contains_duplicate_matches(group):
        match_ids = group['MatchID']
        return len(match_ids) > len(match_ids.drop_duplicates())

    lineups_with_same_match = lineup_pool.groupby("LineupID").apply(contains_duplicate_matches).sum()

    # Summary statistics for lineup pool
    pool_summary = lineup_pool.groupby("LineupID").agg(
        TotalProjection=("Projection", "sum"),
        TotalSalary=("Salary", "sum")
    )
    pool_stats = {
        "Average Projection": pool_summary["TotalProjection"].mean(),
        "Min Projection": pool_summary["TotalProjection"].min(),
        "Max Projection": pool_summary["TotalProjection"].max(),
        "Average Salary": pool_summary["TotalSalary"].mean(),
        "Min Salary": pool_summary["TotalSalary"].min(),
        "Max Salary": pool_summary["TotalSalary"].max(),
    }

    # Summary statistics for selected lineups
    if not selected_lineups.empty:
        selected_summary = selected_lineups.groupby("LineupID").agg(
            TotalProjection=("Projection", "sum"),
            TotalSalary=("Salary", "sum")
        )
        selected_stats = {
            "Average Projection": selected_summary["TotalProjection"].mean(),
            "Min Projection": selected_summary["TotalProjection"].min(),
            "Max Projection": selected_summary["TotalProjection"].max(),
            "Average Salary": selected_summary["TotalSalary"].mean(),
            "Min Salary": selected_summary["TotalSalary"].min(),
            "Max Salary": selected_summary["TotalSalary"].max(),
        }
    else:
        selected_stats = None

    # Display the results
    logging.info("\n=== Lineup Pool Summary ===")
    for key, value in pool_stats.items():
        logging.info(f"{key}: {value:.2f}")

    logging.info(f"Duplicate Lineups in Pool: {duplicate_count}")
    logging.info(f"Lineups with Players from the Same Match: {lineups_with_same_match}")

    if selected_stats:
        logging.info("\n=== Selected Lineup Set Summary ===")
        for key, value in selected_stats.items():
            logging.info(f"{key}: {value:.2f}")
    else:
        logging.info("No selected lineups to summarize.")
