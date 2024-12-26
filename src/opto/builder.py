from pulp import LpProblem, LpVariable, LpMaximize, lpSum, LpStatus
import logging
import pandas as pd


def build_lineup(projection_set, salary_cap, roster_size):
    """
    Builds a single lineup while checking for validity.

    Args:
        projection_set (pd.DataFrame): The player pool with projections and salaries.
        salary_cap (int): The maximum salary cap for the lineup.
        roster_size (int): The number of players required in the lineup.

    Returns:
        pd.DataFrame: The selected lineup as a subset of the projection set.
    """
    # Create the LP problem
    prob = LpProblem("Lineup_Optimization", LpMaximize)

    # Decision variables
    player_vars = LpVariable.dicts("Player", projection_set.index, cat='Binary')

    # Objective: Maximize projected score
    prob += lpSum(projection_set.loc[i, 'Projection'] * player_vars[i] for i in projection_set.index)

    # Constraints
    prob += lpSum(projection_set.loc[i, 'Salary'] * player_vars[i] for i in projection_set.index) <= salary_cap
    prob += lpSum(player_vars[i] for i in projection_set.index) == roster_size

    prob.solve()

    if LpStatus[prob.status] != 'Optimal':
        raise ValueError("No optimal lineup could be created.")

    selected_indices = [i for i in projection_set.index if player_vars[i].varValue == 1]
    lineup = projection_set.loc[selected_indices].copy()

    return lineup


def build_lineups(projection_sets, salary_cap, roster_size, large_pool_size):
    """
    Builds multiple lineups by generating a large pool.

    Returns:
        pd.DataFrame: The larger pool of all generated lineups with full details.
    """
    candidate_lineups = []
    lineup_hashes = set()

    for projection_set in projection_sets:
        try:
            lineup = build_lineup(projection_set, salary_cap, roster_size)

            # Generate a unique hash for the lineup
            lineup_hash = tuple(sorted(lineup['Player'].tolist()))
            if lineup_hash not in lineup_hashes:
                lineup['LineupID'] = len(candidate_lineups) + 1  # Assign a unique LineupID
                lineup_hashes.add(lineup_hash)
                candidate_lineups.append(lineup)
        except ValueError as e:
            logging.warning(f"Skipped lineup due to error: {e}")

        if len(candidate_lineups) >= large_pool_size:
            break

    if candidate_lineups:
        return pd.concat(candidate_lineups, ignore_index=True)
    else:
        return pd.DataFrame()
    return larger_pool


def run_builder(projection_sets, salary_cap, roster_size, large_pool_size):
    """
    Wrapper for the lineup builder.

    Args:
        projection_sets (list of pd.DataFrame): List of projection sets.
        salary_cap (int): The maximum salary cap for each lineup.
        roster_size (int): The number of players required in each lineup.
        large_pool_size (int): The size of the larger lineup pool.

    Returns:
        pd.DataFrame: The larger pool of all generated lineups.
    """
    logging.info("Starting lineup builder...")

    # Build a larger pool of lineups
    larger_pool = build_lineups(projection_sets, salary_cap, roster_size, large_pool_size)

    return larger_pool
