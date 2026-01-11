# Helper functions
import pandas as pd
import numpy as np

from config import PROGRESSION_CATEGORIES
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

