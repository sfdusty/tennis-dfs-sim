import pandas as pd
from src.utils.logger import setup_logger

logger = setup_logger("stat_utils")

def calculate_percentile_baseline(stats_df, percentile=20):
    """Calculate baseline stats based on the given percentile."""
    baseline_stats = stats_df.quantile(percentile / 100).to_dict()
    logger.info(f"Calculated baseline stats at {percentile}th percentile: {baseline_stats}")
    return baseline_stats

def calculate_stat_bounds(stats_df, stats_to_bound):
    """Calculate bounds for the specified stats."""
    bounds = {}
    for stat in stats_to_bound:
        if stat in stats_df.columns:
            lower = stats_df[stat].quantile(0.01)
            upper = stats_df[stat].quantile(0.99)
            bounds[stat] = (lower, upper)
    logger.info(f"Calculated stat bounds: {bounds}")
    return bounds
