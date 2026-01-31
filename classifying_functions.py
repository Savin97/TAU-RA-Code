import pandas as pd
import numpy as np

def classify_movement_SAWI(diff):
    """
        Gets a diff between two rows in the root column.
        Returns a classification of the diff.
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
    
def classify_movement_fine(diff):
    if pd.isna(diff):
        return np.nan
    diff = int(diff)

    if diff in {3, -1, -4}:
        return "S_dia"
    elif diff in {1, 2, 4, 5, -2, -3, -5}:
        return "WA_dia"
    elif diff in {6, 10, -8}:
        return "S_chr"
    elif diff in {7, 8, 9, -6, -7, -9, -10}:
        return "WA_chr"
    else:
        return "!"
