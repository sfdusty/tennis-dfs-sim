# src/sim/game_simulation.py

from src.sim.variance import apply_variance, apply_in_match_variance, STAT_DIRECTIONALITY
from src.sim.dk_scoring import calculate_dk_score
import random
import numpy as np

def calculate_server_edge(server, returner):
    """
    Calculates the probability of the server winning a game based on player stats.

    Args:
        server (dict): Server's stats.
        returner (dict): Returner's stats.

    Returns:
        float: Calculated server edge probability between 0.0 and 1.0.
    """
    # Calculate serve effectiveness
    first_serve_success = server.get("FirstServePercentage", 0.5) * server.get("FirstServeWonPercentage", 0.5)
    second_serve_success = (1 - server.get("FirstServePercentage", 0.5)) * server.get("SecondServeWonPercentage", 0.5)
    serve_effectiveness = first_serve_success + second_serve_success

    # Calculate return effectiveness
    return_effectiveness = returner.get("ReturnPointsWonPercentage", 0.3)

    # Server edge formula (simplified)
    server_edge = serve_effectiveness * (1 - return_effectiveness)
    return max(min(server_edge, 0.99), 0.01)  # Clamp between 0.01 and 0.99 to avoid extremes

def simulate_game(server, returner, expected_service_games):
    """
    Simulates a single game, returning the winner, number of aces, and double faults.

    Args:
        server (dict): Server's stats.
        returner (dict): Returner's stats.
        expected_service_games (int): Expected number of service games per match.

    Returns:
        tuple: (Winner of the game, Aces by server, Double Faults by server)
    """
    # Calculate the server's edge using available stats
    first_serve_success = server.get("FirstServePercentage", 0.5) * server.get("FirstServeWonPercentage", 0.5)
    second_serve_success = (1 - server.get("FirstServePercentage", 0.5)) * server.get("SecondServeWonPercentage", 0.5)
    serve_effectiveness = first_serve_success + second_serve_success

    return_effectiveness = (returner.get("FirstServeReturnPointsWonPercentage", 0.3) +
                            returner.get("SecondServeReturnPointsWonPercentage", 0.3)) / 2

    # Server edge formula
    server_edge = serve_effectiveness * (1 - return_effectiveness)
    server_edge = max(min(server_edge, 0.99), 0.01)  # Clamp between 0.01 and 0.99

    # Determine the game winner
    game_winner = server["Player"] if random.random() < server_edge else returner["Player"]

    # Calculate per-game expected aces and double faults
    aces_per_match = server.get("AcePercentage", 0) * expected_service_games
    double_faults_per_match = server.get("DoubleFaultsPerServiceGame", 0) * expected_service_games

    # Avoid division by zero
    expected_service_games = max(expected_service_games, 1)

    # Per-game expected values
    lambda_aces = aces_per_match / expected_service_games
    lambda_double_faults = double_faults_per_match / expected_service_games

    # Simulate number of aces and double faults using Poisson distribution
    aces = np.random.poisson(lam=lambda_aces)
    double_faults = np.random.poisson(lam=lambda_double_faults)

    return game_winner, aces, double_faults

def simulate_set(player1, player2, expected_service_games):
    """
    Simulates a single set.

    Args:
        player1 (dict): Player 1 stats.
        player2 (dict): Player 2 stats.
        expected_service_games (int): Expected number of service games per match.

    Returns:
        tuple: (Games won by Player 1, Games won by Player 2, Breaks by Player 1, Breaks by Player 2)
    """
    player1_games, player2_games = 0, 0
    player1_breaks, player2_breaks = 0, 0

    while True:
        # Alternate server every game
        if (player1_games + player2_games) % 2 == 0:
            server, returner = player1, player2
        else:
            server, returner = player2, player1

        game_winner, aces, double_faults = simulate_game(server, returner, expected_service_games)

        # Update games won
        if game_winner == player1["Player"]:
            player1_games += 1
            if server["Player"] != player1["Player"]:
                player1_breaks += 1
        else:
            player2_games += 1
            if server["Player"] != player2["Player"]:
                player2_breaks += 1

        # Update Aces and Double Faults
        stats = {}  # Initialize stats for this set
        server_stats = stats.setdefault(server["Player"], {"Aces": 0, "DoubleFaults": 0})
        server_stats["Aces"] += aces
        server_stats["DoubleFaults"] += double_faults

        # Check if set is won
        if max(player1_games, player2_games) >= 6 and abs(player1_games - player2_games) >= 2:
            break

    return player1_games, player2_games, player1_breaks, player2_breaks

def simulate_match(player1, player2, pre_match_variance, in_match_variance):
    """
    Simulates a full match and calculates DraftKings scores.

    Args:
        player1 (dict): Player 1 base stats.
        player2 (dict): Player 2 base stats.
        pre_match_variance (float): Pre-match variance factor.
        in_match_variance (float): In-match variance factor.

    Returns:
        tuple: (player1_score, player2_score, match_winner)
    """
    # Apply pre-match variance
    player1 = apply_variance(player1, pre_match_variance)
    player2 = apply_variance(player2, pre_match_variance)

    # Initialize stats
    stats = {
        "games_won": {player1["Player"]: 0, player2["Player"]: 0},
        "sets_won": {player1["Player"]: 0, player2["Player"]: 0},
        "breaks": {player1["Player"]: 0, player2["Player"]: 0},
        "Aces": {player1["Player"]: 0, player2["Player"]: 0},
        "DoubleFaults": {player1["Player"]: 0, player2["Player"]: 0},
    }

    # Flags for bonuses
    player1_clean_set = False
    player2_clean_set = False
    player1_straight_set = False
    player2_straight_set = False

    # Expected number of service games per match (Best of 3 sets)
    # Assuming roughly 10 service games per player per match
    expected_service_games = 10

    # Simulate Best of 3 sets
    player1_sets, player2_sets = 0, 0
    for _ in range(3):
        if max(player1_sets, player2_sets) == 2:
            break

        # Apply in-match variance
        player1_in_match = apply_in_match_variance(player1, in_match_variance)
        player2_in_match = apply_in_match_variance(player2, in_match_variance)

        # Simulate a set
        p1_games, p2_games, p1_breaks, p2_breaks = simulate_set(player1_in_match, player2_in_match, expected_service_games)
        stats["games_won"][player1["Player"]] += p1_games
        stats["games_won"][player2["Player"]] += p2_games
        stats["breaks"][player1["Player"]] += p1_breaks
        stats["breaks"][player2["Player"]] += p2_breaks

        # Check for clean set bonus (6-0)
        if p1_games == 6 and p2_games == 0:
            player1_clean_set = True
        if p2_games == 6 and p1_games == 0:
            player2_clean_set = True

        # Assign set wins
        if p1_games > p2_games:
            player1_sets += 1
            stats["sets_won"][player1["Player"]] += 1
        else:
            player2_sets += 1
            stats["sets_won"][player2["Player"]] += 1

    # Determine if match was won in straight sets
    if player1_sets == 2 and player2_sets == 0:
        player1_straight_set = True
    if player2_sets == 2 and player1_sets == 0:
        player2_straight_set = True

    # Determine the winner
    match_winner = player1["Player"] if player1_sets > player2_sets else player2["Player"]

    # Prepare match-specific stats for bonuses
    match_stats = {
        "clean_set": player1_clean_set if match_winner == player1["Player"] else player2_clean_set,
        "straight_set": player1_straight_set if match_winner == player1["Player"] else player2_straight_set,
    }

    # Calculate DraftKings scores
    p1_score = calculate_dk_score(
        player=player1,
        stats=stats,
        match_stats=match_stats if match_winner == player1["Player"] else {}
    )
    p2_score = calculate_dk_score(
        player=player2,
        stats=stats,
        match_stats=match_stats if match_winner == player2["Player"] else {}
    )

    return p1_score, p2_score, match_winner
