import pandas as pd
import numpy as np
from collections import Counter
from config import (SAWINONE_PROG_CATEGORIES)

def get_uncond_probs(global_transition_counts):
    # Unconditional Probabilities - sums to 1 over all cells
    total_transitions = float(np.nansum(global_transition_counts.to_numpy()))
    uncond_probs = (global_transition_counts / total_transitions) if total_transitions else global_transition_counts.astype(float)
    return uncond_probs

def piece_progression_type_distribution(df, score, categories) -> pd.Series:
    """
        Returns a Series with percentages of each progression type label for ONE piece.
        Index = labels, values = percentages (0..1).
        sample output:
        S    0.54
        I    0.28
        W    0.18
    """
    total_prog_strength_counts = df["progression_type_simple"].dropna()
    # 2 columns: counts of all prog types for this piece
    counts = total_prog_strength_counts.value_counts()
    # ensure all labels exist
    counts = counts.reindex(categories, fill_value=0)
    total = counts.sum()
    if total == 0:
        return pd.Series({lab: 0.0 for lab in categories}, name=str(score))
    return (counts / total).rename(str(score))

def build_composer_prog_dist_df(piece_prog_type_dist_rows):
    composer_prog_type_dist_df = pd.DataFrame(piece_prog_type_dist_rows)
    # nicer column order
    dist_cols = ["composer", "piece"] + [c for c in SAWINONE_PROG_CATEGORIES if c in composer_prog_type_dist_df.columns]
    composer_prog_type_dist_df = composer_prog_type_dist_df.reindex(columns=dist_cols)
    return composer_prog_type_dist_df
    
def build_composer_prog_trans_df(piece_prog_type_trans_rows):
    composer_prog_type_trans_df = pd.DataFrame(piece_prog_type_trans_rows)
    composer_prog_type_trans_df = composer_prog_type_trans_df.fillna(0.0)
    return composer_prog_type_trans_df

def aggregate_progression_distribution(dist_df: pd.DataFrame, categories):
    """
        Takes dist_df (piece-level percentages) and produces composer-level percentages.
        IMPORTANT: averaging percentages weights pieces equally. 
    """
    label_cols = [c for c in categories if c in dist_df.columns]
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
def all_root_prog_transition_counts(df) -> Counter: #-> pd.DataFrame:
    """
        Build a transition-count matrix of root_change -> next root_change.
        This is different from the S/W/A categorization: it uses the *raw* diff values.
        By default it returns a 21x21 matrix over {-10..-1, 1..10} (excludes 0).
    """
    root_diff = df["root_diff"].dropna().astype(int)
    current = root_diff.iloc[:-1].to_numpy()
    next = root_diff.iloc[1:].to_numpy()
    return Counter(zip(current,next))
