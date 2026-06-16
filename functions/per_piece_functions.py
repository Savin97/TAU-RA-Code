# functions/per_piece_functions.py
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from config import UNNECESSARY_COLS
from functions.utilities import frac_to_float

def drop_unnecessary_columns(df):
    return df.drop(columns=UNNECESSARY_COLS, errors="ignore")

def add_root_prog(df):
    df["root_prog"] = df["root"].diff()
    return df

def convert_frac_cols_to_float(df):
    frac_cols = ["mc_onset", "mn_onset", "timesig"]
    frac_cols_numeric = ["mc_onset_numeric", "mn_onset_numeric", "timesig_numeric"]
    for i in range(len(frac_cols)):
        if frac_cols[i] in df.columns:
            df[frac_cols_numeric[i]] = df[frac_cols[i]].apply(frac_to_float)
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

def add_bigram_prog_weight(df):
    df["bigram_prog_weight"] = df["prog_weight"].shift(1) + df["prog_weight"]
    return df

def add_n_gram(df, n):
    col_name = f"{n}-gram_progs"
    df[col_name] = [
        tuple(int(v) for v in window) if i >= n-1 and not window.isna().any() else None
        for i in range(len(df))
        for window in [df["root_prog"].iloc[i-n+1:i+1]]
    ]
    return df

def add_n_gram_weighed(df, n):
    col_name = f"{n}-gram_weight"

    df[col_name] = [
        df["prog_weight"].iloc[i-n+1:i+1].sum()
        if i >= n-1 and not df["prog_weight"].iloc[i-n+1:i+1].isna().any()
        else None
        for i in range(len(df))
    ]

    return df

def get_weighted_ngrams(df, n):
    gram_col = f"{n}-gram_progs"
    weight_col = f"{n}-gram_weight"
    valid = df[[gram_col, weight_col]].dropna()
    result = defaultdict(float)
    if valid.empty:
        return result
    w_min = valid[weight_col].min()
    w_max = valid[weight_col].max()
    denom = (w_max - w_min) if w_max > w_min else 1.0
    for gram, weight in zip(valid[gram_col], valid[weight_col]):
        result[gram] += (weight - w_min) / denom
    return result

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
# WEIGHTED PROGRESSIONS
# ----------------------

def count_weighted_root_progs(df):
    # Keep alignment across columns, coerce bad values to NaN
    root_prog = pd.to_numeric(df["root_prog"], errors="coerce")
    prog_weight = pd.to_numeric(df["bigram_prog_weight"], errors="coerce")
    prev = root_prog.shift(1)
    current = root_prog
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