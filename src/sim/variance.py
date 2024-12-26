import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define stat directionality: "positive" means higher is better, "negative" means lower is better
STAT_DIRECTIONALITY = {
    "FirstServePercentage": "positive",  # Higher serve percentage is better
    "FirstServeWonPercentage": "positive",  # Winning more first serves is better
    "SecondServeWonPercentage": "positive",  # Winning more second serves is better
    "AcePercentage": "positive",  # Higher ace percentage is better
    "DoubleFaultsPerServiceGame": "negative",  # Fewer double faults per game is better
    "BreakPointsFacedPerServiceGame": "negative",  # Fewer break points faced is better
    "BreakPointsSavedPercentage": "positive",  # Higher break points saved percentage is better
    "FirstServeReturnPointsWonPercentage": "positive",  # Winning more first serve return points is better
    "SecondServeReturnPointsWonPercentage": "positive",  # Winning more second serve return points is better
    "ReturnGamesWonPercentage": "positive",  # Winning more return games is better
    "AceAgainstPercentage": "negative",  # Lower ace against percentage is better
    "BreakPointsConvertedPercentage": "positive",  # Converting break points is better
}

def apply_variance(player, variance_factor):
    """
    Applies symmetric variance to a player's stats using a normal distribution.

    Args:
        player (dict): Player stats as a dictionary.
        variance_factor (float): Variance multiplier (standard deviation factor).

    Returns:
        dict: Adjusted player stats.
    """
    adjusted_player = player.copy()
    for stat, value in player.items():
        if isinstance(value, (float, int)) and stat in STAT_DIRECTIONALITY:
            direction = STAT_DIRECTIONALITY[stat]

            # Calculate standard deviation based on variance_factor
            std_dev = max(variance_factor * abs(value), 0.0)  # Ensure std_dev is non-negative

            # Apply symmetric variance
            try:
                adjustment = np.random.normal(loc=0, scale=std_dev)
            except ValueError as e:
                logging.error(f"Error generating normal distribution for {stat}: {e}")
                adjustment = 0

            if direction == "negative":
                # For negative stats, a higher value is worse
                # Therefore, positive adjustment increases the stat (bad), negative decreases it (good)
                adjusted_player[stat] += adjustment
            elif direction == "positive":
                # For positive stats, a higher value is better
                # Therefore, positive adjustment increases the stat (good), negative decreases it (bad)
                adjusted_player[stat] += adjustment

            # Clamp percentage stats between 0 and 1
            if "Percentage" in stat:
                adjusted_player[stat] = min(max(adjusted_player[stat], 0.0), 1.0)

            # Clamp other stats as necessary (e.g., no negative values for aces or faults)
            if "Ace" in stat or "DoubleFaultsPerServiceGame" in stat:
                adjusted_player[stat] = max(adjusted_player[stat], 0.0)

            # Log the adjustment
            logging.debug(f"Adjusted {stat} by {adjustment:.2f}, new value: {adjusted_player[stat]:.2f}")

    return adjusted_player

def apply_in_match_variance(player, variance_factor):
    """
    Applies variance during the match.

    Args:
        player (dict): Player stats as a dictionary.
        variance_factor (float): Variance multiplier.

    Returns:
        dict: Adjusted player stats.
    """
    return apply_variance(player, variance_factor)
