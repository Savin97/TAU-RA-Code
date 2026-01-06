# Helper functions
import pandas as pd
import numpy as np
import re

from config import PROGRESSION_CATEGORIES

def load_tsv(score):
    return pd.read_csv(score, sep="\t")

# def load_tsv(score):
#     return pd.read_csv(f"{score}_reviewed.tsv", sep="\t")

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


# Statistics summary code (not currently used)
# summary_list = []

# for score in scores:
#     df = load_tsv(score)
#     df_with_root_prog = root_progression(df_reviewed)

#     counts = df_with_root_prog["progression_strength"].value_counts()
#     props = counts / counts.sum()

#     # store row
#     row = {"piece": score}
#     for c in PROGRESSION_CATEGORIES:
#         row[f"Proprotion of {c}"] = props.get(c, 0)
#     summary_list.append(row)

#     df_with_root_prog.to_csv(f"{score}_with_root_prog.tsv", sep="\t", index = False)

# prop_summary = pd.DataFrame(summary_list).set_index("piece").fillna(0)


# prop_summary.to_csv("summary.tsv", sep="\t", index=False)