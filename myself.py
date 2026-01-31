import pandas as pd
import numpy as np
from pathlib import Path

from config import ROOT_PATH

def myself():
    ROOT = Path(ROOT_PATH)
    repos = [
        "bach_en_fr_suites",
        "bach_solo",
        "beethoven_piano_sonatas",
        "ABC",
        "chopin_mazurkas",
        "mozart_piano_sonatas",
        "liszt_pelerinage"
    ]

    all_reviewed_tsv_files = []
    bach_tsv_files = []
    mozart_tsv_files = []
    beethoven_tsv_files = []
    chopin_tsv_files = []
    liszt_tsv_files = []

    # Loop through each repository and collect reviewed TSV files
    for repo in repos:
        reviewed_dir = ROOT / repo / "reviewed"
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

    # Dict with composer name and their corresponding tsv files list
    composer_dict = {
        "Bach": bach_tsv_files,
        "Mozart": mozart_tsv_files,
        "Beethoven": beethoven_tsv_files,
        "Chopin": chopin_tsv_files,
        "Liszt": liszt_tsv_files,
        "All": all_reviewed_tsv_files
    }


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
    
def classify_movement_

def add_root_diff(df):
    df["root_diff"] = df["root"].diff()
    df["progression_type"] = df["root_diff"].apply(classify_movement_SAWI)




myself()