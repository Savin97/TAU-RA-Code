from pathlib import Path
import pandas as pd

def use_sanity():
    tsv = Path("sanity.csv")
    print("Loading df...")
    df = pd.read_csv(tsv)
    print("df loaded")
    # Fix numbers as dates
    # mapping Excel-date strings back to time values
    fix_map = {
        "01-Apr": "1/4",
        "02-Apr": "2/4",
        "03-Apr": "3/4",
        "04-Apr": "4/4",
        "01-Feb": "1/2",
        "02-Feb": "2/2",
        "01-Aug": "1/8",
        "02-Aug": "2/8",
        "03-Aug": "3/8",
        "04-Aug": "4/8",
        "0": "0"
    }

    df["mc_onset"] = df["mc_onset"].astype(str).replace(fix_map)
    df["timesig"] = df["timesig"].astype(str).replace(fix_map)
    return df