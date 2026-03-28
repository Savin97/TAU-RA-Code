import pandas as pd
import numpy as np
from collections import Counter

def rootdiff_bigram_prog_weight_matrix(df: pd.DataFrame):
    """
    Returns a fixed (diff_max-diff_min+1) x (diff_max-diff_min+1) matrix:
      index = prev_root_diff
      cols  = curr_root_diff
      values = sum(bigram_prog_weight) over all transitions

    Transition i is from row i-1 -> row i, weighted by row i's bigram_prog_weight.
    """
    root_col: str = "root_diff"
    weight_col: str = "bigram_prog_weight"
    diff_min: int = -10
    diff_max: int = 10

    d = df.copy()
    
    # Need previous + current root_diff
    prev_root = d[root_col].shift(1)
    curr_root = d[root_col]

    # Assemble transitions; row i represents prev(i-1) -> curr(i) with weight at i
    trans = pd.DataFrame({
        "prev": prev_root,
        "curr": curr_root,
        "w": d[weight_col]
    }).dropna(subset=["prev", "curr", "w"])

    # force int bins (since root_diff should be integer categories)
    trans["prev"] = trans["prev"].astype(int)
    trans["curr"] = trans["curr"].astype(int)

    # fixed category set (21 values if diff_min=-10, diff_max=10)
    cats = list(range(diff_min, diff_max + 1))

    # group and pivot into matrix
    mat = (
        trans.groupby(["prev", "curr"])["w"]
             .sum()
             .unstack(fill_value=0.0)
    )

    # enforce full 21x21 grid even if some diffs never appear
    mat = mat.reindex(index=cats, columns=cats, fill_value=0.0)

    mat.index.name = "prev_root_diff"
    mat.columns.name = "curr_root_diff"
    return mat


def unconditional_joint_probs(mat: pd.DataFrame) -> pd.DataFrame:
    """
        Converts a weighted transition matrix into unconditional joint probabilities
        that sum to 1 across the whole matrix.
    """
    total = float(mat.to_numpy().sum())
    if total == 0.0:
        return mat.astype(float)  # all zeros; nothing to normalize
    return mat.astype(float) / total

def composer_percentages_from_prog_counts(piece_counts_df, categories) -> pd.DataFrame:
    """
        Weighted composer-level percentages:
        sum counts across pieces -> normalize.
    """
    summed = piece_counts_df.groupby("composer")[["n"] + list(categories)].sum()

    denom = summed["n"].replace(0, pd.NA)
    pct = summed.copy()
    for lab in categories:
        pct[lab] = (summed[lab] / denom).fillna(0.0)

    # keep n so you know how much data each composer had
    return pct[["n"] + list(categories)]

def simple_prog_transition_per_piece(df, score, categories) -> pd.Series:
    """
        Returns unconditional transition percentages for ONE piece over the selected categories.
        Output is a flattened Series with index like 'S->A', 'A->W', etc.
        Values sum to 1 across all included transitions (unless total is 0).
    """
    def count_prog_type_per_composer(df, categories):
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

        # Keep only the categories of interest (S, A, W,...)
        cats = list(categories)
        transition_counts = (
            all_transitions
            .reindex(index=cats, columns=cats, fill_value=0)
            .astype(int)
        )
        return transition_counts
    transition_counts = count_prog_type_per_composer(df, categories=categories)

    total = transition_counts.to_numpy().sum()
    if total == 0:
        # return all zeros with consistent index
        idx = [f"{i}->{j}" for i in transition_counts.index for j in transition_counts.columns]
        return pd.Series(0.0, index=idx, name=str(score))

    uncond = transition_counts / total
    # flatten
    out = uncond.stack()
    out.index = [f"{i}->{j}" for (i, j) in out.index]
    out.name = str(score)
    return out

# ----------------------
# WEIGHTED PROGRESSIONS
# ----------------------

def build_all_progs_weighted_matrix(all_progs_bigram_weighted_counts,root_diff_list):
    global_matrix_mat = pd.DataFrame(0.0, index=root_diff_list, columns=root_diff_list)
    for (a, b), val in all_progs_bigram_weighted_counts.items():
        # skip any pairs outside cats if needed
        if a in global_matrix_mat.index and b in global_matrix_mat.columns:
            global_matrix_mat.at[a, b] += float(val)
    global_matrix_mat.index.name = "prev_root_diff"
    global_matrix_mat.columns.name = "curr_root_diff"

    total = float(global_matrix_mat.to_numpy().sum())
    if total == 0.0:
        global_matrix_mat.astype(float)  # all zeros; nothing to normalize
    all_progs_weighted_matrix = global_matrix_mat.astype(float) / total
    return all_progs_weighted_matrix
        