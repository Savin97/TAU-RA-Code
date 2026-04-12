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

def frac_to_float(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    s = str(value).strip()
    if s == "":
        return np.nan
    return float(Fraction(s))  # handles "0", "3/8", "12/8", etc.

def make_frac_not_show_as_date(df):
    pass

def get_SAWINONE_PROG_CATEGORIES_trimmed(global_all_prog_counts):
    # --- TRIM USING COUNTS (not probabilities) ---
    row_ct = global_all_prog_counts.sum(axis=1)
    col_ct = global_all_prog_counts.sum(axis=0)

    # keep states that appear at least once as a source OR a destination
    keep = (row_ct + col_ct) > 0
    counts_trim = global_all_prog_counts.loc[keep, keep]
    cats_trim = counts_trim.index.tolist()
    return cats_trim

def classify_movement_SAWI(diff):
    """
        Gets a diff between two rows in the root column.
        Returns a classification of the diff.
    """
    artificial = {-2, 2, -5, 5, 9, -9}
    strong = {-1, -4, 6, 3, -8, 10}
    weak = {1, 4, -6, -3, 8, -10}
    identical = {0, -0, 7, -7}

    if pd.isna(diff):
        return np.nan

    diff = int(diff)

    if diff in identical:
        return "I"
    elif diff in artificial:
        return "A"
    elif diff in strong:
        return "S"
    elif diff in weak:
        return "W"
    else:
        return "!"
