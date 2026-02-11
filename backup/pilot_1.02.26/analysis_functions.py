# Helper functions
import pandas as pd
import numpy as np
from pathlib import Path

from config import (SIMPLE_PROGRESSION_CATEGORIES, 
                    ALL_PROG_LABELS, 
                    FINE_PROGRESSION_MAP, 
                    FINE_PROGRESSION_LABELS,
                    ROOT_DIFF_VALUES)
from functions.visualization import plot_progression_heatmap

def load_tsv(score):
    """ Simple loader for reviewed tsv files """
    # return pd.read_csv(f"{score}_reviewed.tsv", sep="\t")
    return pd.read_csv(score, sep="\t")

def _counts_from_tsv(tsv_path: Path, labels = SIMPLE_PROGRESSION_CATEGORIES) -> pd.Series:
    """
        Shared core: returns raw counts of progression_strength labels for ONE TSV.
    """
    df = load_tsv(tsv_path)
    dfp = root_progression(df)

    counts = (
        dfp["progression_strength"]
        .value_counts()
        .reindex(labels, fill_value=0)
        .astype(int)
    )
    counts.name = tsv_path.stem
    return counts

def classify_root_movement_classic(diff):
    """
    Coarse classification used throughout the existing codebase.

    Gets difference in root between current and previous chord.
    Returns progression as:
      - "A" (Artificial)
      - "S" (Strong)
      - "W" (Weak)
      - "I" (Identical / no movement)
      - "!" (unexpected / invalid)
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

def build_piece_counts_table(composer_dict: dict, labels=SIMPLE_PROGRESSION_CATEGORIES):
    """
    Returns ONE table: raw counts per piece.
    rows: pieces
    cols: composer, piece, n, A,S,W
    """
    rows = []
    for composer, files in composer_dict.items():
        for p in files:
            p = Path(p)
            counts = _counts_from_tsv(p, labels=labels)
            row = {"composer": composer, "piece": p.stem, "n": int(counts.sum()), **counts.to_dict()}
            rows.append(row)

    df = pd.DataFrame(rows)
    # stable column order
    return df[["composer", "piece", "n"] + list(labels)]


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



def root_progression(df):
    """
    Takes in a score_reviewed.tsv dataframe and returns a dataframe with:

      - root_change: difference from previous root value
      - progression_strength: coarse label in {"A","S","W","I","!"}
      - progression_fine: fine label in {"Sdia","WAdia","Schr","WAchr","identical","!"}

    Notes:
      - progression_strength is the original categorization used elsewhere.
      - progression_fine is the newly requested categorization.
    """
    df = df.copy()

    # difference from previous row
    df["root_change"] = df["root"].diff()

    # existing categorization
    df["progression_strength"] = df["root_change"].apply(classify_root_movement_classic)

    # new categorization
    df["progression_fine"] = df["root_change"].apply(classify_root_movement_classic_fine)

    return df

def prog_type_count(df, categories = SIMPLE_PROGRESSION_CATEGORIES):
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



def progression_probs(df, categories=SIMPLE_PROGRESSION_CATEGORIES):
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
    cats = list(SIMPLE_PROGRESSION_CATEGORIES)
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
    plot_progression_heatmap(f"{composer}_COND", cond_probs,categories=SIMPLE_PROGRESSION_CATEGORIES)
    plot_progression_heatmap(f"{composer}_UNCOND", uncond_probs,categories=SIMPLE_PROGRESSION_CATEGORIES)


def piece_progression_distribution(score_path, labels=SIMPLE_PROGRESSION_CATEGORIES) -> pd.Series:
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


def piece_transition_unconditional(score_path, categories=SIMPLE_PROGRESSION_CATEGORIES) -> pd.Series:
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
    IMPORTANT: averaging percentages weights pieces equally. 
    """
    label_cols = [c for c in SIMPLE_PROGRESSION_CATEGORIES if c in dist_df.columns]
    agg = dist_df.groupby("composer")[label_cols].mean()  # equal weight per piece
    return agg


def aggregate_transition_unconditional(trans_df: pd.DataFrame) -> pd.DataFrame:
    """
    Composer-level average of per-piece unconditional transition distributions (equal weight per piece).
    """
    trans_cols = [c for c in trans_df.columns if c not in ("composer", "piece")]
    agg = trans_df.groupby("composer")[trans_cols].mean()
    return agg



# -------------------------------------------------------------------
# Root-change (diff value) transition matrix (requested 21x21)
# -------------------------------------------------------------------


def root_change_transition_counts(dfp: pd.DataFrame, diffs=ROOT_DIFF_VALUES) -> pd.DataFrame:
    """
    Build a transition-count matrix of root_change -> next root_change.

    This is different from the S/W/A categorization: it uses the *raw* diff values.

    By default it returns a 21x21 matrix over {-10..-1, 1..10} (excludes 0).
    """
    s = dfp["root_change"].dropna().astype(int)
    
    # keep only the diffs we want (default excludes 0)
    s = s[s.isin(diffs)]

    nxt = s.shift(-1)
    nxt = nxt[nxt.isin(diffs)]

    counts = pd.crosstab(s.loc[nxt.index], nxt).reindex(index=diffs, columns=diffs, fill_value=0).astype(int)
    return counts


def root_change_transition_probs(dfp: pd.DataFrame, diffs=ROOT_DIFF_VALUES, row_normalize: bool = True) -> pd.DataFrame:
    """
    Convert root_change_transition_counts into probabilities.

    If row_normalize=True: P(next_diff | current_diff) (rows sum to 1).
    Else: unconditional probabilities over all included transitions (sum of all cells = 1).
    """
    counts = root_change_transition_counts(dfp, diffs=diffs)

    if row_normalize:
        probs = counts.div(counts.sum(axis=1), axis=0).fillna(0.0)
    else:
        total = counts.to_numpy().sum()
        probs = (counts / total) if total else counts.astype(float)

    return probs


def get_root_change_matrices(composer: str, reviewed_tsv_files):
    """
    Aggregate (sum) root-change transition counts across many TSVs and plot both:

      - conditional matrix (rows sum to 1)
      - unconditional matrix (all cells sum to 1)

    Uses plot_progression_heatmap for visualization.
    """
    diffs = list(ROOT_DIFF_VALUES)

    global_counts = pd.DataFrame(0, index=diffs, columns=diffs, dtype=int)

    for score in reviewed_tsv_files:
        df = load_tsv(score)
        dfp = root_progression(df)
        global_counts += root_change_transition_counts(dfp, diffs=diffs)

    cond = global_counts.div(global_counts.sum(axis=1), axis=0).fillna(0.0)

    total = global_counts.to_numpy().sum()
    uncond = (global_counts / total) if total else global_counts.astype(float)

    # --- TRIM USING COUNTS (not probabilities) ---
    row_ct = global_counts.sum(axis=1)
    col_ct = global_counts.sum(axis=0)

    # keep states that appear at least once as a source OR a destination
    keep = (row_ct + col_ct) > 0

    counts_trim = global_counts.loc[keep, keep]
    cats_trim = counts_trim.index.tolist()

    # recompute probs from trimmed counts
    cond_trim = counts_trim.div(counts_trim.sum(axis=1), axis=0).fillna(0.0)

    total = counts_trim.to_numpy().sum()
    uncond_trim = (counts_trim / total) if total else counts_trim.astype(float)
    
    plot_progression_heatmap(
        f"{composer}_DIFF_UNCOND",
        uncond_trim,
        categories=cats_trim
    )
    plot_progression_heatmap(
        f"{composer}_DIFF_COND",
        cond_trim,
        categories=cats_trim
    )

    return global_counts, cond, uncond


def fine_progression_transition_counts(dfp: pd.DataFrame,
                                       col: str = "fine_prog",
                                       labels = None) -> pd.DataFrame:
    if labels is None:
        labels = list(FINE_PROGRESSION_LABELS)

    cur = dfp[col].shift(0)
    nxt = dfp[col].shift(-1)

    tmp = pd.DataFrame({"cur": cur, "nxt": nxt}).dropna()

    counts = pd.crosstab(tmp["cur"], tmp["nxt"])

    # enforce full 5x5 order even if some missing
    counts = counts.reindex(index=labels, columns=labels, fill_value=0)
    return counts


def get_fine_progression_matrices(composer: str, reviewed_tsv_files):
    labels = list(FINE_PROGRESSION_LABELS)
    global_counts = pd.DataFrame(0, index=labels, columns=labels, dtype=int)

    for score in reviewed_tsv_files:
        df = load_tsv(score)
        dfp = root_progression(df)

        # if you didn't add dfp["fine_prog"] inside root_progression, do it here:
        if "fine_prog" not in dfp.columns:
            dfp["fine_prog"] = dfp["root_change"].map(classify_root_movement_classic_fine)

        global_counts += fine_progression_transition_counts(dfp, col="fine_prog", labels=labels)

    cond = global_counts.div(global_counts.sum(axis=1), axis=0).fillna(0.0)

    total = global_counts.to_numpy().sum()
    uncond = (global_counts / total) if total else global_counts.astype(float)

    plot_progression_heatmap(f"{composer}_FINE_COND", cond, categories=labels)
    plot_progression_heatmap(f"{composer}_FINE_UNCOND", uncond, categories=labels)

    return global_counts, cond, uncond

