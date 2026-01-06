from pathlib import Path
from config import OUTPUT_PATH, ROOT_PATH
from analysis_functions import root_progression, load_tsv

def main():
    ROOT = Path(ROOT_PATH)
    repos = [
        "bach_en_fr_suites",
        "bach_solo",
        "debussy_suite_bergamasque",
        "mozart_piano_sonatas",
    ]

    reviewed_tsv_files = []

    for repo in repos:
        reviewed_dir = ROOT / repo / "reviewed"
        reviewed_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))

    print(f"Found {len(reviewed_tsv_files)} reviewed TSV files")

    for score in reviewed_tsv_files:  
        df = load_tsv(score)
        df.to_csv("output/df.csv", sep="\t", index=False)  # overwrite to ensure consistent format
        #df_with_root_prog = root_progression(df)
        break

if __name__ == "__main__":
    main()
