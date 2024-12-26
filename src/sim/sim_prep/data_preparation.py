import pandas as pd
import logging

# Logger setup
def setup_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger("data_preparation")

def load_and_validate_match_context(match_context_csv):
    """Loads and validates the match context file."""
    try:
        df = pd.read_csv(match_context_csv)
        required_columns = ["Name", "Opponent", "Surface", "ImpliedWinPercentage", "League"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing columns: {missing_columns}")
        df.drop_duplicates(subset=["Name", "Opponent", "Surface"], inplace=True)
        # Ensure ImpliedWinPercentage is numeric
        df["ImpliedWinPercentage"] = pd.to_numeric(df["ImpliedWinPercentage"], errors="coerce")
        if df["ImpliedWinPercentage"].isnull().any():
            logger.error("Some ImpliedWinPercentage values could not be converted to numeric.")
            raise ValueError("Invalid ImpliedWinPercentage values in match context.")
        logger.info(f"Loaded match context with {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Error loading match context: {e}")
        raise

def load_stats(atp_csv, wta_csv):
    """Loads and combines ATP and WTA stats."""
    try:
        atp_stats = pd.read_csv(atp_csv)
        wta_stats = pd.read_csv(wta_csv)
        combined_stats = pd.concat([atp_stats, wta_stats], ignore_index=True)

        # Columns to retain
        keep_columns = [
            "Player",
            "Surface",
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
            "BreakPointsConvertedPercentage"
        ]

        # Filter the DataFrame
        combined_stats = combined_stats[keep_columns]

        logger.info(f"Filtered stats with {len(combined_stats)} rows and {len(combined_stats.columns)} columns.")
        return combined_stats
    except Exception as e:
        logger.error(f"Error loading stats: {e}")
        raise

def run_data_preparation(match_context_csv, atp_csv, wta_csv):
    """Run the data preparation process."""
    logger.info("Running data preparation...")
    match_context = load_and_validate_match_context(match_context_csv)
    stats_df = load_stats(atp_csv, wta_csv)
    return match_context, stats_df
