# Helper functions
import pandas as pd
import numpy as np
import re

from config import PROGRESSION_CATEGORIES
from visualization import plot_progression_heatmap

def load_tsv(score):
    # return pd.read_csv(f"{score}_reviewed.tsv", sep="\t")
    return pd.read_csv(score, sep="\t")


def classify_root_movement(d):
    """
        Classifies Root Movement as Artifical (Super strong), Strong, Weak, or I (no movement).
        Returns ! for invalid values.
     """
    artificial = {-2, 2, -5, 5, 9, -9}
    strong = {-1, -4, 6, 3, -8, 10}
    weak = {1, 4, -6, -3, 8, -10}
    identical = {0, -0, 7, -7}
    if pd.isna(d):
        return np.nan
    d = int(d)

    if d in identical:
        return "I"
    elif d in artificial:
        return "A"
    elif d in strong:
        return "S"
    elif d in weak:
        return "W"
    else:
        return "!"
    

def root_progression(df):
    """
        Takes in a score_reviewed.tsv file.

        Adds the columns root_change,  progression_strength.
        root_change = Difference from previous root value.

        progression_strength:
        Classifies Root Movement as Artifical (Super strong), Strong, Weak, or I (no movement).
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

    # Total counts of each symbol
    total_counts = prog_strength.value_counts()

    # Count transitions using crosstab: current vs next
    shifted = prog_strength.shift(-1)
    all_transitions = pd.crosstab(prog_strength, shifted)

    # Keep only the categories of interest (S, A, W)
    cats = list(categories)
    transition_counts = all_transitions.loc[cats, cats].fillna(0).astype(int)
    return total_counts, transition_counts


def progression_probs(df, categories=PROGRESSION_CATEGORIES):
    """
        Compute:
        - total counts of each category
        - how many times each category is followed by each category
            (transition matrix)
        - row-normalized transition probabilities

        Returns (total_counts, transition_counts, transition_probs)
    """
    _, transition_counts = prog_type_count(df, categories)
    # Row-normalized probabilities P(next = j | current = i)
    transition_probs = transition_counts.div(
        transition_counts.sum(axis=1), axis=0
    )

    return transition_probs

def get_transition_probs_from_multiple_scores(composer, reviewed_tsv_files):
    cats = list(PROGRESSION_CATEGORIES)
    global_transition_counts = pd.DataFrame(
        0, index=cats, columns=cats, dtype=int
    )

    for score in reviewed_tsv_files: 
        print(f"Loading {score}...")
        df = load_tsv(score)
        df_with_root_prog = root_progression(df)
        
        # df_with_root_prog.to_csv(OUTPUT / f"WITH_root_prog{score.name}", sep="\t", index=False)
        _, transition_counts = prog_type_count(df_with_root_prog)

        # Accumulate
        global_transition_counts += transition_counts

        # total_counts, transition_counts = prog_type_count(df_with_root_prog)
        # progression_probabilities = progression_probs(df_with_root_prog)
        # print("Total counts of progression types:")
        # print(total_counts.loc[["S", "A", "W"]])
        # print("\nTransition counts (current row -> next row):")
        # print(transition_counts)
        # print("\nTransition probabilities (row-normalized):")
        # print(progression_probabilities)

    
    global_transition_probs = global_transition_counts.div(
            global_transition_counts.sum(axis=1), axis=0
        )
    print(f"Found {len(reviewed_tsv_files)} reviewed TSV files") 
    plot_progression_heatmap(composer, global_transition_probs)
