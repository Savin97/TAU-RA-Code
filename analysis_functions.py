# Helper functions
import pandas as pd
import numpy as np
from pathlib import Path

from config import PROGRESSION_CATEGORIES, ALL_PROG_LABELS
from visualization import plot_progression_heatmap

def load_tsv(score):
    """ Simple loader for reviewed tsv files """
    # return pd.read_csv(f"{score}_reviewed.tsv", sep="\t")
    return pd.read_csv(score, sep="\t")

def classify_root_movement(diff):
    """
        Gets difference in root between current and previous chord.
        Returns progression as A (Artifical), S (Strong), W (Weak), or I (no movement).
        Returns ! for invalid values.
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
    

def root_progression(df):
    """
        Returns a df with some of the original columns from the reviewed files
        and adds columns root_change, progression_strength
        Takes in a score_reviewed.tsv file.
        root_change = Difference from previous root value.
        progression_strength = Classifies Root Movement as Artifical (Super strong), Strong, Weak, or I (no movement).
        Returns ! for invalid values.
    """
    df = df.copy()

    # difference from previous row
    df["root_change"] = df["root"].diff()
    df["progression_strength"] = df["root_change"].apply(classify_root_movement)
    cols_to_keep = ["mc", "mn", "mc_onset", "mn_onset", "label", "chord", "root", "root_change", "progression_strength"]
    df = df[cols_to_keep]

    return df

def prog_type_count(df, categories = PROGRESSION_CATEGORIES):
    """
        Compute total counts of each category
    """
    prog_strength = df["progression_strength"]

    # Total counts of each progression_strength
    total_counts = prog_strength.value_counts()

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

def piece_progression_distribution(score_path, labels=PROGRESSION_CATEGORIES) -> pd.Series:
    """
    Returns a Series with percentages of each progression_strength label for ONE piece.
    Index = labels, values = percentages (0..1).
    """
    df = load_tsv(score_path)
    dfp = root_progression(df)

    s = dfp["progression_strength"].dropna()

    counts = s.value_counts()
    # ensure all labels exist
    counts = counts.reindex(labels, fill_value=0)

    total = counts.sum()
    if total == 0:
        return pd.Series({lab: 0.0 for lab in labels}, name=str(score_path))

    return (counts / total).rename(str(score_path))


def progression_probs(df, categories=PROGRESSION_CATEGORIES):
    """
        Compute:
        - total counts of each category using prog_type_count
        - how many times each category is followed by each category
            (transition matrix)
        - row-normalized transition probabilities

        Returns (total_counts, transition_counts, transition_probs)
    """
    _, transition_counts = prog_type_count(df, categories)

    # Row-normalized probabilities
    transition_probs = transition_counts.div(
        transition_counts.sum(axis=1), axis=0
    )

    return transition_probs

def get_progression_probs(composer, reviewed_tsv_files):
    cats = list(PROGRESSION_CATEGORIES)
    # Initialize global transition counts dataframe 
    global_transition_counts = pd.DataFrame(0, index=cats, columns=cats, dtype=int)

    for score in reviewed_tsv_files:
        # Loop through each score's reviewed tsv file
        # and accumulate transition counts from all scores
        df = load_tsv(score)
        df_with_root_prog = root_progression(df)
        _, transition_counts = prog_type_count(df_with_root_prog)
        global_transition_counts += transition_counts

    # 1) Conditional: (rows sum to 1)
    cond_probs = global_transition_counts.div(
        global_transition_counts.sum(axis=1), axis=0
    ).fillna(0.0)

    # 2) Unconditional:  (sums to 1 over all cells)
    total_transitions = global_transition_counts.to_numpy().sum()
    uncond_probs = (global_transition_counts / total_transitions) if total_transitions else global_transition_counts.astype(float)

    # Save / plot both
    plot_progression_heatmap(f"{composer}_COND", cond_probs)
    plot_progression_heatmap(f"{composer}_UNCOND", uncond_probs)



def piece_progression_distribution(score_path, labels=PROGRESSION_CATEGORIES) -> pd.Series:
    """
    Returns a Series with percentages of each progression_strength label for ONE piece.
    Index = labels, values = percentages (0..1).
    """
    df = load_tsv(score_path)
    dfp = root_progression(df)

    s = dfp["progression_strength"].dropna()

    counts = s.value_counts()
    # ensure all labels exist
    counts = counts.reindex(labels, fill_value=0)

    total = counts.sum()
    if total == 0:
        return pd.Series({lab: 0.0 for lab in labels}, name=str(score_path))

    return (counts / total).rename(str(score_path))


def piece_transition_unconditional(score_path, categories=PROGRESSION_CATEGORIES) -> pd.Series:
    """
    Returns unconditional transition percentages for ONE piece over the selected categories.
    Output is a flattened Series with index like 'S->A', 'A->W', etc.
    Values sum to 1 across all included transitions (unless total is 0).
    """
    df = load_tsv(score_path)
    dfp = root_progression(df)

    _, transition_counts = prog_type_count(dfp, categories=categories)

    total = transition_counts.to_numpy().sum()
    if total == 0:
        # return all zeros with consistent index
        idx = [f"{i}->{j}" for i in transition_counts.index for j in transition_counts.columns]
        return pd.Series(0.0, index=idx, name=str(score_path))

    uncond = transition_counts / total
    # flatten
    out = uncond.stack()
    out.index = [f"{i}->{j}" for (i, j) in out.index]
    out.name = str(score_path)
    return out


def build_piece_level_tables(composer_dict: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    composer_dict: {"Bach": [Path(...), ...], "Mozart": [...], ...}

    Returns:
      dist_df: rows = pieces, cols = A/S/W/I/! (+ composer, piece)
      trans_df: rows = pieces, cols = 'S->A', ... (+ composer, piece)
    """
    dist_rows = []
    trans_rows = []

    for composer, files in composer_dict.items():
        for score_path in files:
            score_path = Path(score_path)

            dist = piece_progression_distribution(score_path)
            dist_rows.append(
                {"composer": composer, "piece": score_path.stem, **dist.to_dict()}
            )

            trans = piece_transition_unconditional(score_path)
            trans_rows.append(
                {"composer": composer, "piece": score_path.stem, **trans.to_dict()}
            )

    dist_df = pd.DataFrame(dist_rows)
    trans_df = pd.DataFrame(trans_rows)

    # Optional: nicer column order
    dist_cols = ["composer", "piece"] + [c for c in ALL_PROG_LABELS if c in dist_df.columns]
    dist_df = dist_df.reindex(columns=dist_cols)

    trans_df = trans_df.fillna(0.0)

    return dist_df, trans_df


def aggregate_progression_distribution(dist_df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes dist_df (piece-level percentages) and produces composer-level percentages.
    IMPORTANT: averaging percentages weights pieces equally. If you want weighting by number of chords,
    store raw counts instead. See note below.
    """
    label_cols = [c for c in PROGRESSION_CATEGORIES if c in dist_df.columns]
    agg = dist_df.groupby("composer")[label_cols].mean()  # equal weight per piece
    return agg


def aggregate_transition_unconditional(trans_df: pd.DataFrame) -> pd.DataFrame:
    """
    Composer-level average of per-piece unconditional transition distributions (equal weight per piece).
    """
    trans_cols = [c for c in trans_df.columns if c not in ("composer", "piece")]
    agg = trans_df.groupby("composer")[trans_cols].mean()
    return agg
