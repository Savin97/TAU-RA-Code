from pathlib import Path
from config import OUTPUT_PATH, ROOT_PATH
from analysis_functions import progression_stats, root_progression, load_tsv
from visualization import plot_progression_heatmap

def main():
    ROOT = Path(ROOT_PATH)
    OUTPUT = Path(OUTPUT_PATH)
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
        df_with_root_prog = root_progression(df)
        df_with_root_prog.to_csv(OUTPUT / f"{score.name}_with_root_prog", sep="\t", index=False)
        total_counts, transition_counts, transition_probs = progression_stats(df_with_root_prog)

        print("Total counts of progression types:")
        print(total_counts.loc[["S", "A", "W"]])

        print("\nTransition counts (current row -> next row):")
        print(transition_counts)

        print("\nTransition probabilities (row-normalized):")
        print(transition_probs)

        df_with_root_prog.to_csv(OUTPUT / score.name, sep="\t", index=False)
        plot_progression_heatmap(transition_probs)
        break

if __name__ == "__main__":
    main()
