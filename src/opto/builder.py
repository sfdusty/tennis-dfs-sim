from pulp import LpProblem, LpVariable, LpMaximize, lpSum, LpStatus
import logging
import pandas as pd


def build_lineup(projection_set, salary_cap, roster_size):
    """Builds a single lineup while checking for validity."""
    # Create the LP problem
    prob = LpProblem("Lineup Optimization", LpMaximize)

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
    lineup = projection_set.loc[selected_indices]
    return lineup


def validate_lineup(lineup):
    """Validates a lineup for match-up constraints."""
    match_ids = lineup['MatchID']
    if len(match_ids) > len(match_ids.drop_duplicates()):
        raise ValueError("Lineup contains players from the same match.")


def build_lineups(projection_sets, salary_cap, roster_size, num_lineups, unique_players_between_lineups):
    """Builds multiple lineups with constraints."""
    built_lineups = []
    all_players = set()

    for projection_set in projection_sets:
        lineup = build_lineup(projection_set, salary_cap, roster_size)
        validate_lineup(lineup)

        lineup_players = set(lineup['Player'])
        if len(all_players & lineup_players) > roster_size - unique_players_between_lineups:
            continue  # Skip lineup if not enough unique players

        built_lineups.append(lineup)
        all_players.update(lineup_players)

    return pd.concat(built_lineups, ignore_index=True)


def run_builder(projection_sets, salary_cap, roster_size, num_lineups, unique_players_between_lineups):
    """Wrapper for the lineup builder."""
    logging.info("Starting lineup builder...")
    return build_lineups(projection_sets, salary_cap, roster_size, num_lineups, unique_players_between_lineups)
