import pandas as pd
from pathlib import Path

from config import SIMPLE_PROGRESSION_CATEGORIES

from classifying_functions import classify_movement_SAWI, classify_movement_fine
def add_root_diff(df):
    df["root_diff"] = df["root"].diff()
    return df

def add_root_progression_type_simple(df):
    df["progression_type_simple"] = df["root_diff"].apply(classify_movement_SAWI)
    return df

def add_root_progression_type_fine(df):
    df["progression_type_fine"] = df["root_diff"].apply(classify_movement_fine)
    return df

def progression_type_count_per_piece(tsv_path, df, labels = SIMPLE_PROGRESSION_CATEGORIES) -> pd.Series:
    """
        Returns raw counts of progression_strength labels for ONE TSV.
    """
    if labels == SIMPLE_PROGRESSION_CATEGORIES:
        counts = (
            df["progression_type_simple"]
            .value_counts()
            .reindex(labels, fill_value=0)
            .astype(int)
        )
    else:
        counts = (
            df["progression_type_fine"]
            .value_counts()
            .reindex(labels, fill_value=0)
            .astype(int)
        )
    counts.name = tsv_path.stem
    return counts



def build_progression_count_per_piece( tsv_path: Path, df, composer, pieces_list: list):
        """
            Returns 1 table: raw counts per piece.
            rows: pieces
            cols: composer, piece, n,A,S,W,I
        """
        counts = progression_type_count_per_piece(tsv_path, df)
        row = {"composer": composer, "piece": tsv_path.stem, "n": int(counts.sum()), **counts.to_dict()}
        return row
        

def piece_percentages_from_counts(piece_counts_df, labels=SIMPLE_PROGRESSION_CATEGORIES):
            """
                Derive piece-level percentages from piece-level counts (no recompute).
            """
            out = piece_counts_df.copy()
            denom = out["n"].replace(0, pd.NA)
            for lab in labels:
                out[lab] = (out[lab] / denom).fillna(0.0)
            return out

def composer_percentages_from_piece_counts(piece_counts_df, labels=SIMPLE_PROGRESSION_CATEGORIES):
    """
        Weighted composer-level percentages:
        sum counts across pieces -> normalize.
    """
    summed = piece_counts_df.groupby("composer")[["n"] + list(labels)].sum()

    denom = summed["n"].replace(0, pd.NA)
    pct = summed.copy()
    for lab in labels:
        pct[lab] = (summed[lab] / denom).fillna(0.0)

    # keep n so you know how much data each composer had
    return pct[["n"] + list(labels)]


def prog_type_count(df, categories = SIMPLE_PROGRESSION_CATEGORIES):
    """
        Compute total counts of each category
    """
    prog_strength = df["progression_strength"]

    # Total counts of each progression_strength
    total_counts = progression_type_count_per_piece("_", df)

    # Count transitions using crosstab: current vs next
    shifted = prog_strength.shift(-1)
    all_transitions = pd.crosstab(prog_strength, shifted)
    # Keep only the categories of interest (S, A, W)
    cats = list(categories)
    transition_counts = (
        all_transitions
        .reindex(index=cats, columns=cats, fill_value=0)
        .astype(int)
    )
    return total_counts, transition_counts



