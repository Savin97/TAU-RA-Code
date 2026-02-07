from pathlib import Path
from config import  ROOT_PATH, ROOT_DIFF_VALUES, FINE_PROGRESSION_LABELS
from analysis_functions import (
    get_progression_probs,
    build_piece_counts_table,
    build_piece_level_tables,
    piece_percentages_from_counts,
    composer_percentages_from_piece_counts,
    aggregate_progression_distribution,
    aggregate_transition_unconditional,
    get_root_change_matrices,
    get_fine_progression_matrices

)
#from visualization import composer_progression_percentage_heatmap

def main():
    """
        Main function to process multiple composers and plot their progression heatmaps.
    """
    ROOT = Path(ROOT_PATH)
    repos = [
        "bach_en_fr_suites",
        "bach_solo",
        "beethoven_piano_sonatas",
        "ABC",
        "chopin_mazurkas",
        "mozart_piano_sonatas",
        "liszt_pelerinage"
    ]

    all_reviewed_tsv_files = []
    bach_tsv_files = []
    mozart_tsv_files = []
    beethoven_tsv_files = []
    chopin_tsv_files = []
    liszt_tsv_files = []

    # Loop through each repository and collect reviewed TSV files
    for repo in repos:
        reviewed_dir = ROOT / repo / "reviewed"
        all_reviewed_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))

        if repo == "bach_en_fr_suites":
            bach_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "bach_solo":
            bach_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "chopin_mazurkas":
            chopin_tsv_files = list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "beethoven_piano_sonatas":
            beethoven_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "ABC":
            beethoven_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "mozart_piano_sonatas":
            mozart_tsv_files = list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "liszt_pelerinage":
            liszt_tsv_files = list(reviewed_dir.rglob("*_reviewed.tsv"))

    # Dict with composer name and their corresponding tsv files list
    composer_dict = {
        "Bach": bach_tsv_files,
        "Mozart": mozart_tsv_files,
        "Beethoven": beethoven_tsv_files,
        "Chopin": chopin_tsv_files,
        "Liszt": liszt_tsv_files,
        "All": all_reviewed_tsv_files
    }

    
    dist_df, trans_df = build_piece_level_tables(composer_dict)

    # Per-piece tables (you can save to CSV)
    dist_df.to_csv("output/piece_progression_percentages.csv", index=False)
    trans_df.to_csv("output/piece_transition_uncond_percentages.csv", index=False)

    # # Composer-level summaries
    # composer_prog = aggregate_progression_distribution(dist_df)
    # composer_trans = aggregate_transition_unconditional(trans_df)


    for composer, tsv_files in composer_dict.items():
        print(f"Processing composer: {composer} with {len(tsv_files)} scores...")
        get_progression_probs(composer, tsv_files)
        # New: 21x21 root-change transition matrices
        get_root_change_matrices(composer, tsv_files)
        get_fine_progression_matrices(composer, tsv_files)


    piece_counts = build_piece_counts_table(composer_dict)
    piece_pct = piece_percentages_from_counts(piece_counts)
    composer_pct = composer_percentages_from_piece_counts(piece_counts)

    piece_pct.to_csv("output/piece_progression_percentages.csv", index=False)
    composer_pct.to_csv("output/composer_progression_percentages.csv")  # composer is index

    print("Wrote: piece_progression_percentages.csv")
    print("Wrote: composer_progression_percentages.csv")
    # TODO: Doesn't work
    # composer_progression_percentage_heatmap(composer_pct)

    print("Done.")

if __name__ == "__main__":
    main()
