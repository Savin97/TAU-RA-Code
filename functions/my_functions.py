import pandas as pd
from pathlib import Path

from config import (ALL_PROG_CATEGORIES,
                    SIMPLE_PROGRESSION_CATEGORIES_URI,
                    SIMPLE_PROGRESSION_CATEGORIES_MARTIN,
                    ALL_PROGRESSION_VALUES_URI,
                    ALL_PROGRESSION_VALUES_MARTIN)

from functions.utilities import classify_movement_SAWI
from functions.visualization import plot_progression_heatmap

def progression_type_count_per_piece(tsv_path, df, labels = SIMPLE_PROGRESSION_CATEGORIES_URI) -> pd.Series:
    """
        Returns raw counts of progression_type labels for ONE TSV.
    """
    if labels == SIMPLE_PROGRESSION_CATEGORIES_URI:
        counts = (
            df["progression_type_simple"]
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
        

def piece_percentages_from_counts(piece_counts_df, labels=SIMPLE_PROGRESSION_CATEGORIES_URI):
            """
                Derive piece-level percentages from piece-level counts (no recompute).
            """
            out = piece_counts_df.copy()
            denom = out["n"].replace(0, pd.NA)
            for lab in labels:
                out[lab] = (out[lab] / denom).fillna(0.0)
            return out

def composer_percentages_from_piece_counts(piece_counts_df, labels=SIMPLE_PROGRESSION_CATEGORIES_URI):
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


def count_prog_type_per_composer(df, categories = SIMPLE_PROGRESSION_CATEGORIES_URI):
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


def row_normalized_progression_probs(df, categories=SIMPLE_PROGRESSION_CATEGORIES_URI):
    """
        Compute:
        - total counts of each category using count_prog_type_per_composer
        - how many times each category is followed by each category
            (transition matrix)
        - row-normalized transition probabilities

        Returns (total_counts, transition_counts, transition_probs)
    """
    transition_counts = count_prog_type_per_composer(df, categories)

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

def piece_progression_type_distribution(df, score, labels = SIMPLE_PROGRESSION_CATEGORIES_URI) -> pd.Series:
    """
        Returns a Series with percentages of each progression type label for ONE piece.
        Index = labels, values = percentages (0..1).
        sample output:
        S    81
        I    41
        A    41
        W    27
    """
    if labels == SIMPLE_PROGRESSION_CATEGORIES_URI:
        total_prog_strength_counts = df["progression_type_simple"].dropna()

    # 2 columns: counts of all prog types for this piece
    counts = total_prog_strength_counts.value_counts()
    # ensure all labels exist
    counts = counts.reindex(labels, fill_value=0)

    total = counts.sum()
    if total == 0:
        return pd.Series({lab: 0.0 for lab in labels}, name=str(score))

    return (counts / total).rename(str(score))

def piece_prog_transition_unconditional(df, score, categories=SIMPLE_PROGRESSION_CATEGORIES_URI) -> pd.Series:
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
    # flatten
    out = uncond.stack()
    out.index = [f"{i}->{j}" for (i, j) in out.index]
    out.name = str(score)
    return out


def build_composer_prog_dist_df(piece_prog_type_dist_rows):
    composer_prog_type_dist_df = pd.DataFrame(piece_prog_type_dist_rows)
    # nicer column order
    dist_cols = ["composer", "piece"] + [c for c in ALL_PROG_CATEGORIES if c in composer_prog_type_dist_df.columns]
    composer_prog_type_dist_df = composer_prog_type_dist_df.reindex(columns=dist_cols)
    return composer_prog_type_dist_df
    
def build_composer_prog_trans_df(piece_prog_type_trans_rows):
    composer_prog_type_trans_df = pd.DataFrame(piece_prog_type_trans_rows)
    composer_prog_type_trans_df = composer_prog_type_trans_df.fillna(0.0)
    return composer_prog_type_trans_df


def aggregate_progression_distribution(dist_df: pd.DataFrame, labels=SIMPLE_PROGRESSION_CATEGORIES_URI):
    """
        Takes dist_df (piece-level percentages) and produces composer-level percentages.
        IMPORTANT: averaging percentages weights pieces equally. 
    """
    label_cols = [c for c in labels if c in dist_df.columns]
    agg = dist_df.groupby("composer")[label_cols].mean()  # equal weight per piece
    return agg


def aggregate_prog_transition_unconditional(trans_df: pd.DataFrame):
    """
        Composer-level average of per-piece unconditional transition distributions (equal weight per piece).
        trans_df is of format
            composer                  piece      S->S      S->A      S->W      A->S      A->A      A->W      W->S      W->A      W->W
        0     Bach      BWV806_01_Prelude  0.292517  0.095238  0.149660  0.142857  0.115646  0.020408  0.108844  0.068027  0.006803
        1     Bach    BWV806_02_Allemande  0.490196  0.166667  0.049020  0.166667  0.078431  0.000000  0.049020  0.000000  0.000000
    """
    trans_cols = [c for c in trans_df.columns if c not in ("composer", "piece")]
    agg = trans_df.groupby("composer")[trans_cols].mean()
    return agg

# -------------------------------------------------------------------
# Root-change (diff value) transition matrix (requested 21x21)
# -------------------------------------------------------------------

def all_root_prog_transition_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
        Build a transition-count matrix of root_change -> next root_change.

        This is different from the S/W/A categorization: it uses the *raw* diff values.

        By default it returns a 21x21 matrix over {-10..-1, 1..10} (excludes 0).
    """
    root_diff = df["root_diff"].dropna().astype(int)
    
    # keep only the diffs we want (default excludes 0)
    root_diff = root_diff[root_diff.isin(ALL_PROGRESSION_VALUES_URI)]
    next_diff = root_diff.shift(-1) # type: ignore
    next_diff = next_diff[next_diff.isin(ALL_PROGRESSION_VALUES_URI)]
    counts = (
        pd.crosstab(root_diff.loc[next_diff.index], next_diff) # type: ignore
        .reindex(index=ALL_PROGRESSION_VALUES_URI, columns=ALL_PROGRESSION_VALUES_URI, fill_value=0)
        .astype(int)
    )
    return counts

def root_prog_transition_probs(df: pd.DataFrame, diffs=ALL_PROGRESSION_VALUES_URI, row_normalize: bool = True) -> pd.DataFrame:
    """
        Convert all_root_prog_transition_counts into probabilities.
        If row_normalize=True: P(next_diff | current_diff) (rows sum to 1).
        Else: unconditional probabilities over all included transitions (sum of all cells = 1).
    """
    counts = all_root_prog_transition_counts(df)

    if row_normalize:
        probs = counts.div(counts.sum(axis=1), axis=0).fillna(0.0)
    else:
        total = counts.to_numpy().sum()
        probs = (counts / total) if total else counts.astype(float)

    return probs

def aggregate_root_progs(composer: str, global_all_prog_counts):
    """
    Aggregate (sum) root-change transition counts across many TSVs and plot both:

      - conditional matrix (rows sum to 1)
      - unconditional matrix (all cells sum to 1)

    Uses plot_progression_heatmap for visualization.
    """
    from functions.visualization import plot_progression_heatmap


    # for score in reviewed_tsv_files:
    #     df = load_tsv(score)
    #     dfp = root_progression(df)
    #     global_counts += all_root_prog_transition_counts(dfp, diffs=diffs)

    total = global_all_prog_counts.to_numpy().sum()
    uncond = (global_all_prog_counts / total) if total else global_all_prog_counts.astype(float)

    # --- TRIM USING COUNTS (not probabilities) ---
    row_ct = global_all_prog_counts.sum(axis=1)
    col_ct = global_all_prog_counts.sum(axis=0)

    # keep states that appear at least once as a source OR a destination
    keep = (row_ct + col_ct) > 0

    counts_trim = global_all_prog_counts.loc[keep, keep]
    cats_trim = counts_trim.index.tolist()

    # recompute probs from trimmed counts

    total = counts_trim.to_numpy().sum()
    uncond_trim = (counts_trim / total) if total else counts_trim.astype(float)

    return uncond_trim
