from pathlib import Path
from config import  ROOT_PATH
from analysis_functions import get_transition_probs_from_multiple_scores

def main():
    ROOT = Path(ROOT_PATH)
    repos = [
        "bach_en_fr_suites",
        "bach_solo",
        "debussy_suite_bergamasque",
        "mozart_piano_sonatas",
    ]

    all_reviewed_tsv_files = []
    bach_tsv_files = []
    debussy_tsv_files = []
    mozart_tsv_files = []
    # global_transitions_by_repo = pd.DataFrame(
    #         0, index=cats, columns=cats, dtype=int
    #     )
    # global_transitions_by_repo[repo] += transition_counts
    for repo in repos:
        reviewed_dir = ROOT / repo / "reviewed"

        all_reviewed_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))
        if repo == "bach_en_fr_suites":
            bach_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "bach_solo":
            bach_tsv_files += list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "debussy_suite_bergamasque":
            debussy_tsv_files = list(reviewed_dir.rglob("*_reviewed.tsv"))
        elif repo == "mozart_piano_sonatas":
            mozart_tsv_files = list(reviewed_dir.rglob("*_reviewed.tsv"))

    get_transition_probs_from_multiple_scores("Bach", bach_tsv_files)
    get_transition_probs_from_multiple_scores("Debussy", debussy_tsv_files)
    get_transition_probs_from_multiple_scores("Mozart", mozart_tsv_files)
    get_transition_probs_from_multiple_scores("Bach, Debussy & Mozart", all_reviewed_tsv_files)



if __name__ == "__main__":
    main()
