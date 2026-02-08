from config import UNNECESSARY_COLS
from functions.utilities import classify_movement_SAWI, classify_movement_fine, frac_to_float

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

def add_root_progression_type_fine(df):
    df["progression_type_fine"] = df["root_diff"].apply(classify_movement_fine)
    return df

def add_annotation_duration(df):
    df["annotation_dur"] = ( 
        ( ( df["mc_onset_numeric"] - df["mc_onset_numeric"].shift(1) )
        + ( df["mc"] - df["mc"].shift(1) ) ) 
        * df["timesig_numeric"]
    )
    return df

def add_prog_weight(df):
    df["prog_weight"] = df["annotation_dur"] + df["annotation_dur"].shift(-1)
    return df

def add_bigram_weight(df):
    df["bigram_weight"] = df["prog_weight"] + df["prog_weight"].shift(1)
    return df

def uri_system_filter(df):
    df = df[df["root"] != df["root"].shift(1)]
    return df

def rootdiff_progweight_sum_table(df) :
    """
        Returns a 2-column table:
        root_diff | prog_weight_sum
    """

    out = (
        df.dropna(subset=["root_diff", "prog_weight"])
          .groupby("root_diff", as_index=False)["prog_weight"]
          .sum()
          .rename(columns={"prog_weight": "prog_weight_sum"})
          .sort_values("root_diff")
          .reset_index(drop=True)
    )
    return out