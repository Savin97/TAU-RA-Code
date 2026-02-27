# functions/per_piece_functions.py
import pandas as pd
import numpy as np
from collections import Counter
from config import UNNECESSARY_COLS
from functions.utilities import classify_movement_SAWI, frac_to_float

def drop_unnecessary_columns(df):
    return df.drop(columns=UNNECESSARY_COLS, errors="ignore")

def convert_frac_cols_to_float(df):
    frac_cols = ["mc_onset", "mn_onset", "timesig"]
    frac_cols_numeric = ["mc_onset_numeric", "mn_onset_numeric", "timesig_numeric"]
    for i in range(len(frac_cols)):
        if frac_cols[i] in df.columns:
            df[frac_cols_numeric[i]] = df[frac_cols[i]].apply(frac_to_float)
    return df

def add_root_diff(df):
    df["root_diff"] = df["root"].diff()
    return df

def add_root_progression_type_simple(df):
    df["progression_type_simple"] = df["root_diff"].apply(classify_movement_SAWI)
    return df

def add_annotation_duration(df):
    df["annotation_dur"] = ( 
        ( ( df["mc_onset_numeric"].shift(-1) - df["mc_onset_numeric"] )
        + ( df["mc"].shift(-1) - df["mc"] ) ) 
        * df["timesig_numeric"]
    )
    return df

def add_prog_weight(df):
    df["prog_weight"] = df["annotation_dur"].shift(1) + df["annotation_dur"]
    return df

def add_bigram_weight(df):
    df["bigram_weight"] = df["prog_weight"].shift(1) + df["prog_weight"]
    return df

def uri_system_filter(df):
    df = df[df["root"] != df["root"].shift(1)]
    return df

def add_proper_empty_last_row(df):
    special_row = pd.DataFrame([{
        "mc": df["mc"].iloc[-1] + 1,
        "mc_onset": 0,
        "timesig": df["timesig"].iloc[-1]
    }])
    df = pd.concat([df, special_row], ignore_index=True)

    return df

# ----------------------
# SIMPLE PROGRESSIONS
# ----------------------

def simple_prog_transition_counts(df, categories, col="progression_type_simple"):
    """
        Return a |cats|x|cats| DataFrame of transition COUNTS:
        rows = current, cols = next.
    """
    prog_type = df[col]
    cur = prog_type
    nxt = prog_type.shift(-1)

    # keep only transitions where both sides are valid categories
    mask = cur.isin(categories) & nxt.isin(categories)
    cur = cur[mask]
    nxt = nxt[mask]

    mat = pd.crosstab(cur, nxt)

    # force exact grid + order
    mat = mat.reindex(index=list(categories), columns=list(categories), fill_value=0).astype(int)
    return mat

def build_progression_count_per_piece(tsv_path, df, composer, labels):
    """
        Returns 1 table: raw counts per piece.
        rows: pieces
        cols: composer, piece, n,A,S,W,I
    """
    counts = (
        df["progression_type_simple"]
        .value_counts()
        .reindex(labels, fill_value=0)
        .astype(int)
    )
    if tsv_path != None:
        counts.name = tsv_path.stem
    row = {"composer": composer, "piece": tsv_path.stem, "n": int(counts.sum()), **counts.to_dict()}
    return row

# ----------------------
# WEIGHTED PROGRESSIONS
# ----------------------

def count_weighted_root_diffs(df):
    # Keep alignment across columns, coerce bad values to NaN
    root_diff = pd.to_numeric(df["root_diff"], errors="coerce")
    prog_weight = pd.to_numeric(df["bigram_weight"], errors="coerce")
    prev = root_diff.shift(1)
    current = root_diff
    mask = prev.notna() & current.notna() & prog_weight.notna()
    if not mask.any():
        return Counter()

    prev_i = prev[mask].astype(int).to_numpy()
    curr_i = current[mask].astype(int).to_numpy()
    weights = prog_weight[mask].to_numpy(dtype=float)
    # Unique rows + weighted sum per unique pair
    pairs = np.column_stack((prev_i, curr_i))
    uniq, inv = np.unique(pairs, axis=0, return_inverse=True)
    sums = np.bincount(inv, weights=weights)

    return Counter({(int(a), int(b)): float(s) for (a, b), s in zip(uniq, sums)})
    root_diff = df["root_diff"].astype("Int64")
    prev = root_diff.shift(1).to_numpy()
    current = root_diff.to_numpy()
    prog_weight = df["bigram_weight"]
    pairs = np.column_stack((prev, current))

    
    uniq, inv = np.unique(pairs, axis=0, return_inverse=True)
    sums = np.bincount(inv, weights=prog_weight)

    return Counter({(np.int64(a), np.int64(b)): float(s) for (a, b), s in zip(uniq, sums)})