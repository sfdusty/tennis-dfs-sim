# src/sim/dk_scoring.py

def calculate_dk_score(player, stats, match_stats):
    """
    Calculates DraftKings score for a player based on official scoring.

    Args:
        player (dict): Player's stats after variance application.
        stats (dict): Aggregated match stats (games_won, sets_won, breaks).
        match_stats (dict): Additional match-specific stats (e.g., clean sets, straight sets).

    Returns:
        float: Calculated DraftKings score.
    """
    score = 0.0

    # Match played
    score += 30

    # Games won and lost
    games_won = stats["games_won"][player["Player"]]
    games_lost = stats["games_won"][player["Opponent"]]
    score += games_won * 2.5
    score -= games_lost * 2

    # Sets won and lost
    sets_won = stats["sets_won"][player["Player"]]
    sets_lost = stats["sets_won"][player["Opponent"]]
    score += sets_won * 6
    score -= sets_lost * 3

    # Match won
    if sets_won > sets_lost:
        score += 6

    # Aces
    aaces = player.get("AcesPerMatch", 0)
    score += aaces * 0.4

    # Double faults
    double_faults = player.get("DoubleFaultsPerMatch", 0)
    score -= double_faults * 1

    # Breaks
    breaks = stats["breaks"][player["Player"]]
    score += breaks * 0.75

    # Clean set bonus (6-0)
    if match_stats.get("clean_set", False):
        score += 4

    # Straight set bonus (win match without losing a set)
    if match_stats.get("straight_set", False):
        score += 6

    # No double fault bonus
    if double_faults == 0:
        score += 2.5

    # 10+ aces bonus
    if aaces >= 10:
        score += 2

    return score
