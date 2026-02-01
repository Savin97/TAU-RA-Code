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


def get_progression_probs(composer, reviewed_tsv_files):
    cats = list(SIMPLE_PROGRESSION_CATEGORIES)
    # Initialize global transition counts dataframe 
    global_transition_counts = pd.DataFrame(0, index=cats, columns=cats, dtype=int)

    # for score in reviewed_tsv_files:
    #     # Loop through each score's reviewed tsv file
    #     # and accumulate transition counts from all scores
    #     df = load_tsv(score)
    #     df_with_root_prog = root_progression(df)
    #     _, transition_counts = prog_type_count(df_with_root_prog)
    #     global_transition_counts += transition_counts

    # # 1) Conditional: (rows sum to 1)
    # cond_probs = global_transition_counts.div(
    #     global_transition_counts.sum(axis=1), axis=0
    # ).fillna(0.0)

    # # 2) Unconditional:  (sums to 1 over all cells)
    # total_transitions = global_transition_counts.to_numpy().sum()
    # uncond_probs = (global_transition_counts / total_transitions) if total_transitions else global_transition_counts.astype(float)

    # # Save / plot both
    # plot_progression_heatmap(f"{composer}_COND", cond_probs,categories=SIMPLE_PROGRESSION_CATEGORIES)
    # plot_progression_heatmap(f"{composer}_UNCOND", uncond_probs,categories=SIMPLE_PROGRESSION_CATEGORIES)



