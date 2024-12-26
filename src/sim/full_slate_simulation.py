# src/sim/full_slate_simulation.py

from src.sim.game_simulation import simulate_match
import pandas as pd
import numpy as np

def run_full_slate_simulations(sim_prepped_df, pre_match_variance, in_match_variance, num_simulations):
    """
    Runs simulations for the entire slate of matches.

    Args:
        sim_prepped_df (pd.DataFrame): Prepped matches data with required columns.
        pre_match_variance (float): Pre-match variance factor.
        in_match_variance (float): In-match variance factor.
        num_simulations (int): Number of simulations per match.

    Returns:
        pd.DataFrame: Summary of simulation results with percentiles and win-loss records.
        pd.DataFrame: Detailed simulation scores for optimizer.
        dict: Win-loss records for all players.
    """
    results = []
    detailed_scores = {}
    win_loss_records = {}

    for match_id, match_data in sim_prepped_df.groupby("MatchID"):
        if len(match_data) < 2:
            print(f"Warning: MatchID {match_id} does not have two players. Skipping.")
            continue

        # Extract player stats
        player1 = match_data.iloc[0].to_dict()
        player2 = match_data.iloc[1].to_dict()

        # Initialize lists to store simulation data
        player1_scores = []
        player2_scores = []
        match_winners = []

        for _ in range(num_simulations):
            # Simulate match
            p1_score, p2_score, match_winner = simulate_match(
                player1, player2, pre_match_variance, in_match_variance
            )
            player1_scores.append(p1_score)
            player2_scores.append(p2_score)
            match_winners.append(match_winner)

        # Calculate statistics for Player 1
        player1_avg = np.mean(player1_scores)
        player1_p10 = np.percentile(player1_scores, 10)
        player1_p25 = np.percentile(player1_scores, 25)
        player1_p50 = np.percentile(player1_scores, 50)
        player1_p75 = np.percentile(player1_scores, 75)
        player1_p90 = np.percentile(player1_scores, 90)
        player1_wins = match_winners.count(player1["Player"])
        player1_losses = num_simulations - player1_wins

        # Calculate statistics for Player 2
        player2_avg = np.mean(player2_scores)
        player2_p10 = np.percentile(player2_scores, 10)
        player2_p25 = np.percentile(player2_scores, 25)
        player2_p50 = np.percentile(player2_scores, 50)
        player2_p75 = np.percentile(player2_scores, 75)
        player2_p90 = np.percentile(player2_scores, 90)
        player2_wins = match_winners.count(player2["Player"])
        player2_losses = num_simulations - player2_wins

        # Append results for Player 1
        results.append({
            "MatchID": match_id,
            "Player": player1["Player"],
            "Average Score": player1_avg,
            "10th Percentile": player1_p10,
            "25th Percentile": player1_p25,
            "50th Percentile (Median)": player1_p50,
            "75th Percentile": player1_p75,
            "90th Percentile": player1_p90,
            "Total Wins": player1_wins,
            "Total Losses": player1_losses,
        })

        # Append results for Player 2
        results.append({
            "MatchID": match_id,
            "Player": player2["Player"],
            "Average Score": player2_avg,
            "10th Percentile": player2_p10,
            "25th Percentile": player2_p25,
            "50th Percentile (Median)": player2_p50,
            "75th Percentile": player2_p75,
            "90th Percentile": player2_p90,
            "Total Wins": player2_wins,
            "Total Losses": player2_losses,
        })

        # Store detailed simulation scores for optimizer
        detailed_scores[player1["Player"]] = player1_scores
        detailed_scores[player2["Player"]] = player2_scores

        # Store win-loss records
        win_loss_records[player1["Player"]] = {"Wins": player1_wins, "Losses": player1_losses}
        win_loss_records[player2["Player"]] = {"Wins": player2_wins, "Losses": player2_losses}

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Convert detailed_scores to DataFrame
    detailed_scores_df = pd.DataFrame.from_dict(detailed_scores, orient="index").transpose()

    return results_df, detailed_scores_df, win_loss_records
