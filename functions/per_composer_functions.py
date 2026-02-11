import pandas as pd

def rootdiff_bigram_weight_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a fixed (diff_max-diff_min+1) x (diff_max-diff_min+1) matrix:
      index = prev_root_diff
      cols  = curr_root_diff
      values = sum(bigram_weight) over all transitions

    Transition i is from row i-1 -> row i, weighted by row i's bigram_weight.
    """
    root_col: str = "root_diff"
    weight_col: str = "bigram_weight"
    diff_min: int = -10
    diff_max: int = 10

    d = df.copy()
    
    # Need previous + current root_diff
    prev_root = d[root_col].shift(1)
    curr_root = d[root_col]

    # Assemble transitions; row i represents prev(i-1) -> curr(i) with weight at i
    trans = pd.DataFrame({
        "prev": prev_root,
        "curr": curr_root,
        "w": d[weight_col]
    }).dropna(subset=["prev", "curr", "w"])

    # force int bins (since root_diff should be integer categories)
    trans["prev"] = trans["prev"].astype(int)
    trans["curr"] = trans["curr"].astype(int)

    # fixed category set (21 values if diff_min=-10, diff_max=10)
    cats = list(range(diff_min, diff_max + 1))

    # group and pivot into matrix
    mat = (
        trans.groupby(["prev", "curr"])["w"]
             .sum()
             .unstack(fill_value=0.0)
    )

    # enforce full 21x21 grid even if some diffs never appear
    mat = mat.reindex(index=cats, columns=cats, fill_value=0.0)

    mat.index.name = "prev_root_diff"
    mat.columns.name = "curr_root_diff"
    return mat

def row_normalize_prog_weight_matrix(mat: pd.DataFrame) -> pd.DataFrame:
    denom = mat.sum(axis=1).replace(0, 1.0)
    return mat.div(denom, axis=0)

def unconditional_joint_probs(mat: pd.DataFrame) -> pd.DataFrame:
    """
        Converts a weighted transition matrix into unconditional joint probabilities
        that sum to 1 across the whole matrix.
    """
    total = float(mat.to_numpy().sum())
    if total == 0.0:
        return mat.astype(float)  # all zeros; nothing to normalize
    return mat.astype(float) / total