import pandas as pd
from rapidfuzz import process, fuzz
from pathlib import Path
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

logger = setup_logger("name_resolution")

def load_name_mapping(names_path):
    if not names_path.exists():
        logger.info(f"Names file '{names_path}' not found. Returning empty mapping.")
        return {}

    try:
        df = pd.read_csv(names_path)
        name_map = pd.Series(df.approved_name.values, index=df.raw_name).to_dict()
        logger.info(f"Loaded name mapping with {len(name_map)} entries.")
        return name_map
    except Exception as e:
        logger.error(f"Error loading names from '{names_path}': {e}")
        return {}

def append_name_mapping(names_path, raw_name, approved_name):
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
        logger.error(f"Error appending name mapping to '{names_path}': {e}")

def fuzzy_match_names(raw_name, choices, threshold=80):
    if not raw_name or not choices:
        logger.error("Invalid input: raw_name or choices is empty.")
        return []

    matches = process.extract(raw_name, choices, scorer=fuzz.WRatio, limit=None)
    filtered_matches = [(match[0], match[1]) for match in matches if match[1] >= threshold]
    return filtered_matches

def save_pending_approval(pending_path, raw_name, candidates):
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
        logger.error(f"Error saving pending approval to '{pending_path}': {e}")

def resolve_names(raw_names, stats_df, names_path, pending_path):
    name_map = load_name_mapping(names_path)
    resolved = {}

    for raw_name in raw_names:
        if raw_name in name_map:
            resolved[raw_name] = name_map[raw_name]
            continue

        candidates = fuzzy_match_names(raw_name, stats_df["Player"].tolist())
        if candidates:
            top_match, score = candidates[0]
            if score >= 80:
                append_name_mapping(names_path, raw_name, top_match)
                resolved[raw_name] = top_match
            else:
                save_pending_approval(pending_path, raw_name, candidates)
        else:
            save_pending_approval(pending_path, raw_name, [])

    logger.info(f"Resolved {len(resolved)} names.")
    return resolved

def run_name_resolution(match_context, stats_df, names_path, pending_path):
    """
    Wrapper for name resolution to integrate resolved names into match context.

    Parameters:
    - match_context (pd.DataFrame): Match context DataFrame.
    - stats_df (pd.DataFrame): Stats DataFrame.
    - names_path (Path): Path to the names mapping file.
    - pending_path (Path): Path to the pending approvals file.

    Returns:
    - pd.DataFrame: Updated match context DataFrame with resolved names.
    """
    logger.info("Running name resolution...")
    raw_names = match_context["Name"].tolist()
    resolved_dict = resolve_names(raw_names, stats_df, names_path, pending_path)

    # Add resolved names to match_context
    match_context["ResolvedName"] = match_context["Name"].map(resolved_dict)
    logger.debug(f"Resolved names added to match context: {match_context[['Name', 'ResolvedName']].head()}")

    return match_context
