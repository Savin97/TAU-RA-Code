import pandas as pd
from pathlib import Path
import numpy as np
from fractions import Fraction

from config import (ROOT_PATH,
                    SIMPLE_PROGRESSION_CATEGORIES_final,
                    SIMPLE_PROGRESSION_CATEGORIES_URI)

def load_tsv(score):
    """ Simple loader for reviewed tsv files """
    # return pd.read_csv(f"{score}_reviewed.tsv", sep="\t")
    return pd.read_csv(score, sep="\t")

def make_csv(df, filename, system, path_modifier):
    # Add a leading apostrophe to columns that might be misinterpreted by Excel
    # So they dont show as dates
    excel_sensitive_cols = ["mc_onset", "mn_onset", "timesig"]
    for col in excel_sensitive_cols:
        if col in df.columns:
            df[col] = "'" + df[col].astype(str)
    if path_modifier == "piece":
        df.to_csv(f"output/{system}/csv/per_piece/{filename}.csv", index=False)
    elif path_modifier == "composer":
        df.to_csv(f"output/{system}/csv/per_composer/{filename}.csv", index=False)
    elif path_modifier == "global":
        df.to_csv(f"output/{system}/csv/global/{filename}.csv", index=False)
    else:
        raise ValueError ("Invalid path_modifier")

def check_dirs(system):
    base = Path("output")
    (base / system / "img").mkdir(parents=True, exist_ok=True)
    (base / system /"csv").mkdir(parents=True, exist_ok=True)
    (base / system /"csv" / "per_piece").mkdir(parents=True, exist_ok=True)
    (base / system /"csv" / "per_composer").mkdir(parents=True, exist_ok=True)
    (base / system /"csv" / "global").mkdir(parents=True, exist_ok=True)

def pick_categories_based_on_system_type(system):
    if system == "final":
        simple_categories = SIMPLE_PROGRESSION_CATEGORIES_final
        print("--------------------\nRunning final's pipeline...\n--------------------")
    elif system == "uri":
        simple_categories = SIMPLE_PROGRESSION_CATEGORIES_URI
        print("--------------------\nRunning Uri's pipeline...\n--------------------")
    else:
        raise ValueError ("Invalid Pipeline System")
    return simple_categories


def create_composer_file_lists(repos):
    ROOT = Path(ROOT_PATH)
    bach_tsv_files, mozart_tsv_files, beethoven_tsv_files, chopin_tsv_files, liszt_tsv_files, all_reviewed_tsv_files = [], [], [], [], [], []
    # Loop through each repository and collect reviewed TSV files
    for repo in repos:
        reviewed_dir = ROOT / "scores" / repo / "reviewed"
        all_reviewed_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))
        if repo == "bach_en_fr_suites":
            bach_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "bach_solo":
            bach_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "chopin_mazurkas":
            chopin_tsv_files = list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "beethoven_piano_sonatas":
            beethoven_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "ABC":
            beethoven_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "mozart_piano_sonatas":
            mozart_tsv_files = list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "liszt_pelerinage":
            liszt_tsv_files = list(reviewed_dir.rglob("*_reviewed.tsv"))
    return bach_tsv_files, mozart_tsv_files, beethoven_tsv_files, chopin_tsv_files, liszt_tsv_files, all_reviewed_tsv_files

def get_uncond_probs(transition_counts):
    # Unconditional Probabilities - sums to 1 over all cells
    total_transitions = float(np.nansum(transition_counts.to_numpy()))
    uncond_probs = (transition_counts / total_transitions) if total_transitions else transition_counts.astype(float)
    return uncond_probs

def frac_to_float(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    s = str(value).strip()
    if s == "":
        return np.nan
    return float(Fraction(s))  # handles "0", "3/8", "12/8", etc.

