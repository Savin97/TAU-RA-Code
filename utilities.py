import pandas as pd
from pathlib import Path
from config import SIMPLE_PROGRESSION_CATEGORIES_URI, FINE_PROGRESSION_CATEGORIES_URI, ALL_PROGRESSION_VALUES_URI

def load_tsv(score):
    """ Simple loader for reviewed tsv files """
    # return pd.read_csv(f"{score}_reviewed.tsv", sep="\t")
    return pd.read_csv(score, sep="\t")

def make_csv(df, filename):
        df.to_csv(f"output/csv/{filename}.csv", index=False)

def check_dirs():
    base = Path("output")
    (base / "img").mkdir(parents=True, exist_ok=True)
    (base / "csv").mkdir(parents=True, exist_ok=True)

def get_diff_categories_trimmed(global_all_prog_counts):
    # --- TRIM USING COUNTS (not probabilities) ---
    row_ct = global_all_prog_counts.sum(axis=1)
    col_ct = global_all_prog_counts.sum(axis=0)

    # keep states that appear at least once as a source OR a destination
    keep = (row_ct + col_ct) > 0
    counts_trim = global_all_prog_counts.loc[keep, keep]
    cats_trim = counts_trim.index.tolist()
    return cats_trim
