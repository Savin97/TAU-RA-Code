from utilities import classify_movement_SAWI, classify_movement_fine

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
    df["annotation_duration"] = df["end_time"] - df["start_time"]
    return df