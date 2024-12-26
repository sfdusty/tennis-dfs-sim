import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Raw Data Files
ATP_CSV = os.path.join(RAW_DATA_DIR, "atp.csv")
WTA_CSV = os.path.join(RAW_DATA_DIR, "wta.csv")
POOL_CSV = os.path.join(RAW_DATA_DIR, "pool.csv")
RAW_NAMES_CSV = os.path.join(RAW_DATA_DIR, "names.csv")

# Processed Data Files
MATCH_CONTEXT_CSV = os.path.join(PROCESSED_DATA_DIR, "match_context.csv")
NAMES_CSV = os.path.join(PROCESSED_DATA_DIR, "names.csv")
PENDING_APPROVALS_CSV = os.path.join(PROCESSED_DATA_DIR, "pending_approvals.csv")
SIM_READY_CSV = os.path.join(PROCESSED_DATA_DIR, "sim_ready.csv")
SIM_RESULTS_CSV = os.path.join(PROCESSED_DATA_DIR, "sim_results.csv")
MANUAL_BASELINES_CSV = os.path.join(PROCESSED_DATA_DIR, "manual_baselines.csv")

# Logging
LOG_FILE = os.path.join(LOGS_DIR, "application.log")

# Configurable Parameters
FUZZY_THRESHOLD = 80  # Minimum threshold for fuzzy name matching
DEFAULT_BASELINE_STATS = {
    "ServiceGamesWonPercentage": 65,
    "ReturnGamesWonPercentage": 35,
    "AcesPerServiceGame": 0.2,
    "DoubleFaultsPerServiceGame": 0.05,
}
