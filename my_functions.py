import pandas as pd
from pathlib import Path

from config import SIMPLE_PROGRESSION_CATEGORIES, FINE_PROGRESSION_LABELS

from utilities import load_tsv

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
        Returns raw counts of progression_type labels for ONE TSV.
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
    if tsv_path != None:
        counts.name = tsv_path.stem
    return counts


def build_progression_count_per_piece( tsv_path: Path, df, composer):
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


def count_prog_type_per_composer(df, categories = SIMPLE_PROGRESSION_CATEGORIES):
    """
        Compute total counts of each category
        returns a table like:
        progression_type_simple     S     A     W     I
        progression_type_simple
        S                        3739  1685  1058  1510
        A                        1597  1422   531   810
        W                        1005   653   135   347
        I                        1709   578   380   777
    """
    prog_strength = df["progression_type_simple"]

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
    return transition_counts


def row_normalized_progression_probs(df, categories=SIMPLE_PROGRESSION_CATEGORIES):
    """
        Compute:
        - total counts of each category using count_prog_type_per_composer
        - how many times each category is followed by each category
            (transition matrix)
        - row-normalized transition probabilities

        Returns (total_counts, transition_counts, transition_probs)
    """
    transition_counts = count_prog_type_per_composer(df, SIMPLE_PROGRESSION_CATEGORIES)

    # Row-normalized probabilities
    transition_probs = transition_counts.div(
        transition_counts.sum(axis=1), axis=0
    )

    return transition_probs

def get_cond_probs(global_transition_counts):
    # Conditional Probabilities - rows sum to 1
    cond_probs = global_transition_counts.div(
        global_transition_counts.sum(axis=1), axis=0
    ).fillna(0.0)
    return cond_probs

def get_uncond_probs(global_transition_counts):
        # Unconditional Probabilities - sums to 1 over all cells
    total_transitions = global_transition_counts.to_numpy().sum()
    uncond_probs = (global_transition_counts / total_transitions) if total_transitions else global_transition_counts.astype(float)
    return uncond_probs

def piece_progression_type_distribution(df, score, labels = SIMPLE_PROGRESSION_CATEGORIES) -> pd.Series:
    """
        Returns a Series with percentages of each progression type label for ONE piece.
        Index = labels, values = percentages (0..1).
        sample output:
        S    81
        I    41
        A    41
        W    27
    """
    if labels == SIMPLE_PROGRESSION_CATEGORIES:
        total_prog_strength_counts = df["progression_type_simple"].dropna()
    elif labels == FINE_PROGRESSION_LABELS:
        total_prog_strength_counts = df["progression_type_fine"].dropna()

    # 2 columns: counts of all prog types for this piece
    counts = total_prog_strength_counts.value_counts()
    # ensure all labels exist
    counts = counts.reindex(labels, fill_value=0)

    total = counts.sum()
    if total == 0:
        return pd.Series({lab: 0.0 for lab in labels}, name=str(score))

    return (counts / total).rename(str(score))

def piece_transition_unconditional(df, score, categories=SIMPLE_PROGRESSION_CATEGORIES) -> pd.Series:
    """
        Returns unconditional transition percentages for ONE piece over the selected categories.
        Output is a flattened Series with index like 'S->A', 'A->W', etc.
        Values sum to 1 across all included transitions (unless total is 0).
    """
    transition_counts = count_prog_type_per_composer(df, categories=categories)

    total = transition_counts.to_numpy().sum()
    if total == 0:
        # return all zeros with consistent index
        idx = [f"{i}->{j}" for i in transition_counts.index for j in transition_counts.columns]
        return pd.Series(0.0, index=idx, name=str(score))

    uncond = transition_counts / total
    # uncond = get_uncond_probs(df) # Doesnt work here
    # flatten
    out = uncond.stack()
    out.index = [f"{i}->{j}" for (i, j) in out.index]
    out.name = str(score)
    return out


# def build_piece_level_tables(composer_dict: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
#     """
#     composer_dict: {"Bach": [Path(...), ...], "Mozart": [...], ...}

#     Returns:
#       dist_df: rows = pieces, cols = A/S/W/I/! (+ composer, piece)
#       trans_df: rows = pieces, cols = 'S->A', ... (+ composer, piece)
#     """
#     dist_rows = []
#     trans_rows = []

#     for composer, files in composer_dict.items():
#         for score_path in files:
#             score_path = Path(score_path)

#             dist = piece_progression_type_distribution(df, score)
#             dist_rows.append(
#                 {"composer": composer, "piece": score_path.stem, **dist.to_dict()}
#             )

#             trans = piece_transition_unconditional(df, score)
#             trans_rows.append(
#                 {"composer": composer, "piece": score_path.stem, **trans.to_dict()}
#             )

#     dist_df = pd.DataFrame(dist_rows)
#     trans_df = pd.DataFrame(trans_rows)

#     # Optional: nicer column order
#     dist_cols = ["composer", "piece"] + [c for c in ALL_PROG_LABELS if c in dist_df.columns]
#     dist_df = dist_df.reindex(columns=dist_cols)

#     trans_df = trans_df.fillna(0.0)

#     return dist_df, trans_df


def aggregate_progression_distribution(dist_df: pd.DataFrame):
    """
    Takes dist_df (piece-level percentages) and produces composer-level percentages.
    IMPORTANT: averaging percentages weights pieces equally. 
    """
    label_cols = [c for c in SIMPLE_PROGRESSION_CATEGORIES if c in dist_df.columns]
    agg = dist_df.groupby("composer")[label_cols].mean()  # equal weight per piece
    return agg


def aggregate_transition_unconditional(trans_df: pd.DataFrame):
    """
    Composer-level average of per-piece unconditional transition distributions (equal weight per piece).
    """
    trans_cols = [c for c in trans_df.columns if c not in ("composer", "piece")]
    agg = trans_df.groupby("composer")[trans_cols].mean()
    return agg
