import streamlit as st
import pandas as pd
from src.sim.main import run_simulation_pipeline
from src.opto.opto_main import run_optimizer_pipeline
import os

# File paths
SIM_PREPPED_CSV = "data/processed/sim_prepped.csv"
SIM_READY_CSV = "data/processed/sim_ready.csv"
IWP_ADJUSTMENTS_CSV = "data/processed/iwp_adjustments.csv"
SIMULATION_RESULTS_CSV = "data/processed/simulation_results.csv"
SIMULATION_DETAILS_CSV = "data/processed/simulation_details.csv"
PLAYER_POOL_CSV = "data/raw/pool2.csv"
OPTIMIZED_LINEUPS_CSV = "data/processed/optimized_lineups.csv"

# ----- Streamlit Configuration -----
st.set_page_config(layout="wide", page_title="Tennis Simulator and Optimizer Admin Panel")

# ----- Helper Functions -----
def load_csv(file_path):
    """Loads a CSV file into a pandas DataFrame."""
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
        return pd.DataFrame()

def save_csv(dataframe, file_path):
    """Saves a pandas DataFrame to a CSV file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        dataframe.to_csv(file_path, index=False)
    except Exception as e:
        st.error(f"Error saving {file_path}: {e}")

# ----- Tabbed Tables -----
st.title("Tennis Simulator and Optimizer Admin Panel")
tabs = st.tabs([
    "Sim Prepped", "Sim Ready", "IWP Adjustments", "Simulation Results", 
    "Win-Loss Records", "Optimizer Details", "Optimized Lineups"
])

# Display `sim_prepped.csv`
with tabs[0]:
    st.header("Sim Prepped Matches")
    sim_prepped_df = load_csv(SIM_PREPPED_CSV)
    st.dataframe(sim_prepped_df, use_container_width=True)

# Display `sim_ready.csv`
with tabs[1]:
    st.header("Sim Ready Matches")
    sim_ready_df = load_csv(SIM_READY_CSV)
    st.dataframe(sim_ready_df, use_container_width=True)

# Display `iwp_adjustments.csv`
with tabs[2]:
    st.header("IWP Adjustments")
    iwp_adjustments_df = load_csv(IWP_ADJUSTMENTS_CSV)
    st.dataframe(iwp_adjustments_df, use_container_width=True)

# ----- Simulation Settings -----
st.sidebar.header("Simulation Parameters")
pre_match_variance = st.sidebar.slider("Pre-Match Variance", 0.0, 1.0, 0.5, 0.05)
in_match_variance = st.sidebar.slider("In-Match Variance", 0.0, 0.5, 0.2, 0.05)
num_simulations = st.sidebar.slider("Number of Simulations", 100, 5000, 1000, 100)

# ----- Optimizer Settings -----
st.sidebar.header("Optimizer Parameters")
bucket_size = st.sidebar.slider("Bucket Size (Diversity)", 1, 1000, 1, 1)
num_lineups = st.sidebar.slider("Number of Lineups", 1, 150, 10, 1)
salary_cap = 50000  # DraftKings salary cap

# ----- Run Simulations -----
if st.button("Run Full-Slate Simulations"):
    st.write("Running simulations for all matches...")
    if sim_prepped_df.empty:
        st.error("Sim Prepped file is empty or not loaded.")
    else:
        try:
            with st.spinner("Simulating..."):
                simulation_results, sim_details, win_loss_records = run_simulation_pipeline(
                    sim_prepped_df=sim_prepped_df,
                    pre_match_variance=pre_match_variance,
                    in_match_variance=in_match_variance,
                    num_simulations=num_simulations,
                )
            st.success("Simulations completed successfully!")

            # Save the results
            save_csv(simulation_results, SIMULATION_RESULTS_CSV)
            save_csv(sim_details, SIMULATION_DETAILS_CSV)

        except Exception as e:
            st.error(f"Error during simulation: {e}")

# ----- Run Optimizer -----
if st.button("Run Optimizer"):
    st.write("Running optimizer...")
    try:
        with st.spinner("Optimizing lineups..."):
            optimized_lineups = run_optimizer_pipeline(
                simulation_details_path=SIMULATION_DETAILS_CSV,
                player_pool_path=PLAYER_POOL_CSV,
                bucket_size=bucket_size,
                num_lineups=num_lineups,
                salary_cap=salary_cap
            )
        st.success("Optimizer completed successfully!")

        # Save the optimized lineups
        save_csv(optimized_lineups, OPTIMIZED_LINEUPS_CSV)

        # Display Optimized Lineups in Tab
        with tabs[6]:
            st.header("Optimized Lineups")
            st.dataframe(optimized_lineups, use_container_width=True)

    except Exception as e:
        st.error(f"Error during optimization: {e}")
