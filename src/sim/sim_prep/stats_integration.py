import pandas as pd
from src.config import SIM_READY_CSV
from src.utils.logger import setup_logger

logger = setup_logger("stats_integration")


def calculate_percentile_baseline(stats_df, percentile=20):
    """
    Calculates baseline stats for unmatched players based on a given percentile,
    accounting for whether lower or higher values are better.
    """
    try:
        logger.info(f"Calculating {percentile}th percentile baseline for stats.")
        
        # Define directionality for stats
        directionality = {
            "FirstServePercentage": "higher",
            "FirstServeWonPercentage": "higher",
            "SecondServeWonPercentage": "higher",
            "AcePercentage": "higher",
            "DoubleFaultsPerServiceGame": "lower",
            "BreakPointsFacedPerServiceGame": "lower",
            "BreakPointsSavedPercentage": "higher",
            "FirstServeReturnPointsWonPercentage": "higher",
            "SecondServeReturnPointsWonPercentage": "higher",
            "ReturnGamesWonPercentage": "higher",
            "AceAgainstPercentage": "lower",
            "BreakPointsConvertedPercentage": "higher",
        }

        # Validate required columns
        missing_columns = [col for col in directionality if col not in stats_df.columns]
        if missing_columns:
            logger.error(f"Missing columns in stats_df for baseline calculation: {missing_columns}")
            raise ValueError(f"Missing columns for baseline calculation: {missing_columns}")

        # Convert required columns to numeric
        for col in directionality:
            stats_df[col] = pd.to_numeric(stats_df[col], errors="coerce")

        # Drop rows with NaN in required columns
        stats_df.dropna(subset=directionality.keys(), inplace=True)

        # Calculate the percentile baseline
        baseline = {}
        for stat, direction in directionality.items():
            if direction == "higher":
                baseline[stat] = stats_df[stat].quantile(percentile / 100)
            elif direction == "lower":
                baseline[stat] = stats_df[stat].quantile((100 - percentile) / 100)

        logger.info(f"Calculated baseline stats: {baseline}")
        return baseline
    except Exception as e:
        logger.error(f"Error calculating percentile baseline: {e}")
        raise


def calculate_stat_bounds(stats_df, columns):
    """
    Calculates bounds (min, max) for specified stats columns.
    """
    try:
        # Filter to numerical columns only
        numerical_columns = stats_df[columns].select_dtypes(include=["number"]).columns
        logger.info(f"Calculating stat bounds for numerical columns: {numerical_columns}")

        # Drop rows with NaN in required columns
        stats_df.dropna(subset=numerical_columns, inplace=True)

        # Calculate bounds
        bounds = {col: (stats_df[col].min(), stats_df[col].max()) for col in numerical_columns}
        logger.info(f"Calculated bounds: {bounds}")
        return bounds
    except Exception as e:
        logger.error(f"Error calculating stat bounds: {e}")
        raise


def adjust_stats_with_iwp(stats, iwp, bounds, baseline_iwp=50.0, adjustment_strength=1.0):
    """
    Adjust stats based on the player's implied win percentage (IWP) and clamp them.
    
    Parameters:
    - stats (dict): Player stats to adjust.
    - iwp (float): Player's implied win percentage (0-100).
    - bounds (dict): Bounds for clamping stats.
    - baseline_iwp (float): Neutral baseline for IWP (default: 50).
    - adjustment_strength (float): Multiplier to scale IWP adjustment influence (default: 1.0).
    
    Returns:
    - dict: Adjusted and clamped stats.
    - str: Direction of IWP adjustment ("Positive", "Negative", "Neutral").
    """
    # Scaling constants
    SCALING_FACTORS = {
        "FirstServePercentage": 0.05,
        "FirstServeWonPercentage": 0.05,
        "SecondServeWonPercentage": 0.05,
        "AcePercentage": 0.1,
        "DoubleFaultsPerServiceGame":.1,
        "BreakPointsFacedPerServiceGame": -0.05,
        "BreakPointsSavedPercentage": 0.05,
        "FirstServeReturnPointsWonPercentage": 0.05,
        "SecondServeReturnPointsWonPercentage": 0.05,
        "ReturnGamesWonPercentage": 0.05,
        "AceAgainstPercentage": -0.05,
        "BreakPointsConvertedPercentage": 0.05,
    }

    # Normalize deviation to [-0.5, 0.5]
    deviation = (iwp - baseline_iwp) / 100
    adjustment_direction = "Neutral"
    if deviation > 0:
        adjustment_direction = "Positive"
    elif deviation < 0:
        adjustment_direction = "Negative"

    # Adjust stats with scaling and adjustment strength
    adjusted_stats = {
        col: stats[col] * (1 + deviation * SCALING_FACTORS[col] * adjustment_strength)
        for col in stats.keys() if col in SCALING_FACTORS
    }

    # Clamp stats to bounds
    clamped_stats = {
        key: max(bounds[key][0], min(bounds[key][1], value))
        for key, value in adjusted_stats.items()
    }

    return clamped_stats, adjustment_direction


def integrate_stats_and_save(match_context, stats_df, sourced_strength=0.1, estimated_strength=0.1):
    """
    Integrates stats into the match context and saves the simulation-ready files.
    """
    try:
        # Validate and normalize match_context columns
        match_context["ResolvedName"] = match_context["ResolvedName"].astype(str).str.strip()
        match_context["Surface"] = match_context["Surface"].astype(str).str.strip()

        # Calculate baseline stats and bounds
        baseline_stats = calculate_percentile_baseline(stats_df, percentile=20)
        numerical_columns = [
            "FirstServePercentage",
            "FirstServeWonPercentage",
            "SecondServeWonPercentage",
            "AcePercentage",
            "DoubleFaultsPerServiceGame",
            "BreakPointsFacedPerServiceGame",
            "BreakPointsSavedPercentage",
            "FirstServeReturnPointsWonPercentage",
            "SecondServeReturnPointsWonPercentage",
            "ReturnGamesWonPercentage",
            "AceAgainstPercentage",
            "BreakPointsConvertedPercentage",
        ]
        bounds = calculate_stat_bounds(stats_df, numerical_columns)

        final_rows = []
        simplified_rows = []
        adjustment_rows = []  # To store IWP adjustments for each player
        match_id = 1

        for i in range(0, len(match_context), 2):  # Process pairs of rows for each match
            player_row = match_context.iloc[i]
            opponent_row = match_context.iloc[i + 1]

            for row, opponent in [(player_row, opponent_row), (opponent_row, player_row)]:
                resolved_name = str(row.get("ResolvedName", "")).strip()
                surface = str(row.get("Surface", "")).strip()
                iwp = row.get("ImpliedWinPercentage", 50)

                if not resolved_name:
                    logger.warning(f"No resolved name for row: {row}")
                    stats = baseline_stats
                    stats_source = "Estimated"
                    adjustment_strength = estimated_strength
                else:
                    # Attempt to filter stats for the specific surface
                    player_stats = stats_df[
                        (stats_df["Player"] == resolved_name) & (stats_df["Surface"] == surface)
                    ]

                    if player_stats.empty:
                        logger.warning(f"No stats found for {resolved_name} on {surface}. Using baseline stats.")
                        stats = baseline_stats
                        stats_source = "Estimated"
                        adjustment_strength = estimated_strength
                    else:
                        stats = player_stats.iloc[0].to_dict()
                        stats_source = "Sourced"
                        adjustment_strength = sourced_strength

                # Adjust and clamp stats based on IWP
                adjusted_stats, iwp_adjustment = adjust_stats_with_iwp(
                    stats, iwp, bounds, baseline_iwp=50.0, adjustment_strength=adjustment_strength
                )

                # Calculate changes for each stat
                stat_changes = {key: adjusted_stats[key] - stats[key] for key in numerical_columns if key in stats}
                stat_changes["Player"] = row["Name"]
                stat_changes["Surface"] = surface
                stat_changes["IWP"] = iwp
                adjustment_rows.append(stat_changes)

                # Prepare full simulation-ready row
                full_row = {
                    "Name": row["Name"],
                    "Opponent": opponent["Name"],
                    "Surface": surface,
                    "League": row["League"],
                    **adjusted_stats,
                    "StatsSource": stats_source,
                    "IWPAdjustment": iwp_adjustment,
                    "MatchID": match_id,
                }
                final_rows.append(full_row)

                # Prepare simplified row
                simplified_row = {
                    "MatchID": match_id,
                    "Player": row["Name"],
                    "Opponent": opponent["Name"],
                    **adjusted_stats,
                }
                simplified_rows.append(simplified_row)

            match_id += 1  # Increment MatchID after processing both players

        # Save the full simulation-ready file
        final_df = pd.DataFrame(final_rows)
        final_df.to_csv(SIM_READY_CSV, index=False)
        logger.info(f"Simulation-ready file saved with {len(final_df)} rows.")

        # Save the simplified version
        simplified_csv_path = SIM_READY_CSV.replace("sim_ready.csv", "sim_prepped.csv")
        simplified_df = pd.DataFrame(simplified_rows)
        simplified_df.to_csv(simplified_csv_path, index=False)
        logger.info(f"Simplified simulation-prepped file saved as '{simplified_csv_path}' with {len(simplified_df)} rows.")

        # Save the IWP adjustment impacts
        adjustments_df = pd.DataFrame(adjustment_rows)
        adjustments_csv_path = SIM_READY_CSV.replace("sim_ready.csv", "iwp_adjustments.csv")
        adjustments_df.to_csv(adjustments_csv_path, index=False)
        logger.info(f"IWP adjustments file saved as '{adjustments_csv_path}' with {len(adjustments_df)} rows.")

    except Exception as e:
        logger.error(f"Error integrating stats: {e}")
        raise


def run_stats_integration(match_context, stats_df, sourced_strength=0.1, estimated_strength=0.1):
    """
    Runs the stats integration process.
    
    Parameters:
    - match_context (pd.DataFrame): Resolved match context.
    - stats_df (pd.DataFrame): Combined stats DataFrame.
    - sourced_strength (float): Adjustment strength for sourced stats.
    - estimated_strength (float): Adjustment strength for estimated stats.
    """
    logger.info("Running stats integration...")
    integrate_stats_and_save(
        match_context,
        stats_df,
        sourced_strength=sourced_strength,
        estimated_strength=estimated_strength
    )
