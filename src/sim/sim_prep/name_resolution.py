import pandas as pd
from rapidfuzz import process, fuzz
from pathlib import Path
from src.config import NAMES_CSV, PENDING_APPROVALS_CSV
from src.utils.logger import setup_logger

logger = setup_logger("name_resolution")

names_path = Path(NAMES_CSV)
pending_path = Path(PENDING_APPROVALS_CSV)

def load_name_mapping():
    if not names_path.exists():
        logger.info(f"Names file '{NAMES_CSV}' not found. Returning empty mapping.")
        return {}

    try:
        df = pd.read_csv(names_path)
        name_map = pd.Series(df.approved_name.values, index=df.raw_name).to_dict()
        logger.info(f"Loaded name mapping with {len(name_map)} entries.")
        return name_map
    except Exception as e:
        logger.error(f"Error loading names from '{NAMES_CSV}': {e}")
        return {}

def append_name_mapping(raw_name, approved_name):
    logger.debug(f"Appending name mapping: {raw_name} -> {approved_name}")
    try:
        if names_path.exists():
            df = pd.read_csv(names_path)
        else:
            df = pd.DataFrame(columns=["raw_name", "approved_name"])

        new_mapping = {"raw_name": raw_name, "approved_name": approved_name}
        df = pd.concat([df, pd.DataFrame([new_mapping])], ignore_index=True)
        df.drop_duplicates(subset=["raw_name"], inplace=True)
        df.to_csv(names_path, index=False)
        logger.info(f"Appended name mapping: {new_mapping}")
    except Exception as e:
        logger.error(f"Error appending name mapping to '{NAMES_CSV}': {e}")

def fuzzy_match_names(raw_name, choices, threshold=80):
    if not raw_name or not choices:
        logger.error("Invalid input: raw_name or choices is empty.")
        return []

    matches = process.extract(raw_name, choices, scorer=fuzz.WRatio, limit=None)
    filtered_matches = [(match[0], match[1]) for match in matches if match[1] >= threshold]
    return filtered_matches

def save_pending_approval(raw_name, candidates):
    logger.debug(f"Saving pending approval for '{raw_name}' with candidates {candidates}.")
    try:
        if pending_path.exists():
            df = pd.read_csv(pending_path)
        else:
            df = pd.DataFrame(columns=["raw_name", "candidates"])

        candidates_str = ";".join([f"{match} ({score})" for match, score in candidates])
        new_entry = {"raw_name": raw_name, "candidates": candidates_str}
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.drop_duplicates(subset=["raw_name"], inplace=True)
        df.to_csv(pending_path, index=False)
        logger.info(f"Saved pending approval: {new_entry}")
    except Exception as e:
        logger.error(f"Error saving pending approval to '{PENDING_APPROVALS_CSV}': {e}")

def resolve_names(raw_names, stats_df):
    name_map = load_name_mapping()
    resolved = {}

    for raw_name in raw_names:
        if raw_name in name_map:
            resolved[raw_name] = name_map[raw_name]
            continue

        candidates = fuzzy_match_names(raw_name, stats_df["Player"].tolist())
        if candidates:
            top_match, score = candidates[0]
            if score >= 80:
                append_name_mapping(raw_name, top_match)
                resolved[raw_name] = top_match
            else:
                save_pending_approval(raw_name, candidates)
        else:
            save_pending_approval(raw_name, [])

    logger.info(f"Resolved {len(resolved)} names.")
    return resolved

def run_name_resolution(match_context, stats_df):
    """
    Wrapper for name resolution to integrate resolved names into match context.

    Parameters:
    - match_context (pd.DataFrame): Match context DataFrame.
    - stats_df (pd.DataFrame): Stats DataFrame.

    Returns:
    - pd.DataFrame: Updated match context DataFrame with resolved names.
    """
    logger.info("Running name resolution...")
    raw_names = match_context["Name"].tolist()
    resolved_dict = resolve_names(raw_names, stats_df)

    # Add resolved names to match_context
    match_context["ResolvedName"] = match_context["Name"].map(resolved_dict)
    logger.debug(f"Resolved names added to match context: {match_context[['Name', 'ResolvedName']].head()}")

    return match_context
