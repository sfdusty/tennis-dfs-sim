# src/sim/main.py

from src.sim.full_slate_simulation import run_full_slate_simulations

def run_simulation_pipeline(sim_prepped_df, pre_match_variance, in_match_variance, num_simulations):
    """
    Orchestrates the simulation process for the entire slate of matches.

    Args:
        sim_prepped_df (pd.DataFrame): Original prepped matches data.
        pre_match_variance (float): Pre-match variance factor.
        in_match_variance (float): In-match variance factor.
        num_simulations (int): Number of simulations per match.

    Returns:
        pd.DataFrame: Summary of simulation results with percentiles and win-loss records.
        pd.DataFrame: Detailed simulation scores for optimizer.
        dict: Win-loss records for all players.
    """
    # Run the full slate simulations
    return run_full_slate_simulations(
        sim_prepped_df=sim_prepped_df,
        pre_match_variance=pre_match_variance,
        in_match_variance=in_match_variance,
        num_simulations=num_simulations
    )
