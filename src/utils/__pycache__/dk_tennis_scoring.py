DK_POINTS_MATCH_PLAYED = 30
DK_POINTS_MATCH_WIN = 6
DK_POINTS_SET_WIN = 6
DK_POINTS_GAME_WIN = 2.5
DK_POINTS_GAME_LOST = -2
DK_POINTS_BREAK_CONVERTED = 0.75


def calculate_dk_score(player, opponent, stats, is_winner):
    """
    Calculates a player's DraftKings score based on match statistics.

    Args:
        player (dict): Player stats.
        opponent (dict): Opponent stats.
        stats (dict): Match stats.
        is_winner (bool): Whether the player won the match.

    Returns:
        float: DraftKings score.
    """
    score = DK_POINTS_MATCH_PLAYED  # Base points for playing a match

    if is_winner:
        score += DK_POINTS_MATCH_WIN
        score += stats["sets_won"][player["Player"]] * DK_POINTS_SET_WIN

    # Points for games won and lost
    score += stats["games_won"][player["Player"]] * DK_POINTS_GAME_WIN
    score += stats["games_won"][opponent["Player"]] * DK_POINTS_GAME_LOST

    # Points for breaks converted
    score += stats["breaks"][player["Player"]] * DK_POINTS_BREAK_CONVERTED

    return score
