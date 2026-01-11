from pathlib import Path
from config import  ROOT_PATH
from analysis_functions import get_progression_probs

def main():
    """
        Main function to process multiple composers and plot their progression heatmaps.
    """
    ROOT = Path(ROOT_PATH)
    repos = [
        "bach_en_fr_suites",
        "bach_solo",
        "beethoven_piano_sonatas",
        "chopin_mazurkas",
        "mozart_piano_sonatas"
    ]

    all_reviewed_tsv_files = []
    bach_tsv_files = []
    mozart_tsv_files = []
    beethoven_tsv_files = []
    chopin_tsv_files = []

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
            beethoven_tsv_files = list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "mozart_piano_sonatas":
            mozart_tsv_files = list(reviewed_dir.rglob("*_reviewed.tsv"))

    # Dict with composer name and their corresponding tsv files list
    composer_dict = {
        "Bach": bach_tsv_files,
        "Mozart": mozart_tsv_files,
        "Beethoven": beethoven_tsv_files,
        "Chopin": chopin_tsv_files,
        "All": all_reviewed_tsv_files
    }

    for composer, tsv_files in composer_dict.items():
        print(f"Processing composer: {composer} with {len(tsv_files)} scores...")
        get_progression_probs(composer, tsv_files)

if __name__ == "__main__":
    main()
