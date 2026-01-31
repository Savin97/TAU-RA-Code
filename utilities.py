import pandas as pd

from config import SIMPLE_PROGRESSION_CATEGORIES

def load_tsv(score):
    """ Simple loader for reviewed tsv files """
    # return pd.read_csv(f"{score}_reviewed.tsv", sep="\t")
    return pd.read_csv(score, sep="\t")

def prog_type_count(df, categories = SIMPLE_PROGRESSION_CATEGORIES):
    """
        Gets a df of one piece
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