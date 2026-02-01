import pandas as pd
from pathlib import Path

from config import ROOT_PATH, SIMPLE_PROGRESSION_CATEGORIES
from utilities import load_tsv
from my_functions import (add_root_diff,
                        add_root_progression_type_simple,
                        add_root_progression_type_fine,
                        build_progression_count_per_piece,
                        composer_percentages_from_piece_counts,
                        piece_percentages_from_counts,
                        count_prog_type_per_composer,
                        row_normalized_progression_probs)

from visualization import plot_progression_heatmap

def myself():
    """
        1. Get tsv files in a list of paths.
        2. Run a loop for each composer and create a DF for each composer.
        3. On these DFs, perform the analysis, create features.
    """
    ROOT = Path(ROOT_PATH)
    repos = [
        "bach_en_fr_suites",
        "bach_solo",
        # "beethoven_piano_sonatas",
        # "ABC",
        # "chopin_mazurkas",
        # "mozart_piano_sonatas",
        # "liszt_pelerinage"
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
        # "Mozart": mozart_tsv_files,
        # "Beethoven": beethoven_tsv_files,
        # "Chopin": chopin_tsv_files,
        # "Liszt": liszt_tsv_files,
        # "All": all_reviewed_tsv_files
    }

    for composer, tsv_files in composer_dict.items():
        print(f"Processing composer: {composer} with {len(tsv_files)} scores...")
        progression_count_per_piece_per_composer = []
        piece_dfs=[]
        global_transition_counts = pd.DataFrame(0, 
                                                index=list(SIMPLE_PROGRESSION_CATEGORIES), 
                                                columns=list(SIMPLE_PROGRESSION_CATEGORIES), 
                                                dtype=int)

        for tsv in tsv_files:
            # Loop through each score's reviewed tsv file
            # Add root difference
            # Add root progression types
            # and accumulate transition counts from all scores
            path = Path(tsv)
            
            df = load_tsv(path)
            df = add_root_diff(df)
            df = add_root_progression_type_simple(df)
            df = add_root_progression_type_fine(df)

            progression_count_per_piece = build_progression_count_per_piece(path, df, composer)
            progression_count_per_piece_per_composer.append(progression_count_per_piece)

            global_transition_counts += row_normalized_progression_probs(df)
            piece_dfs.append(df)
        
        composer_df = pd.DataFrame()
        for piece in piece_dfs:
            composer_df = pd.concat([composer_df,piece], ignore_index=True)

        transition_counts_per_composer = count_prog_type_per_composer(composer_df)
        print(transition_counts_per_composer)
        
        prog_count_per_piece = pd.DataFrame(progression_count_per_piece_per_composer)
        # stable column order
        prog_count_per_piece = prog_count_per_piece[["composer", "piece", "n"] + list(SIMPLE_PROGRESSION_CATEGORIES) ]
        piece_level_prog_percentages = piece_percentages_from_counts(prog_count_per_piece)
        prog_count_per_composer = composer_percentages_from_piece_counts(prog_count_per_piece)

        # Might be unused:row_normalized_progression_probs(composer, tsv_files)

        # Conditional Probabilities - rows sum to 1
        cond_probs = global_transition_counts.div(
            global_transition_counts.sum(axis=1), axis=0
        ).fillna(0.0)

        
        # Unconditional Probabilities - sums to 1 over all cells
        total_transitions = global_transition_counts.to_numpy().sum()
        uncond_probs = (global_transition_counts / total_transitions) if total_transitions else global_transition_counts.astype(float)

        # Save / plot both
        plot_progression_heatmap(f"{composer}_COND", cond_probs, categories=SIMPLE_PROGRESSION_CATEGORIES)
        plot_progression_heatmap(f"{composer}_UNCOND", uncond_probs, categories=SIMPLE_PROGRESSION_CATEGORIES)




        # Output to .csv
        prog_count_per_piece.to_csv(f"output/csv/{composer}_piece_counts.csv",index=False)
        piece_level_prog_percentages.to_csv(f"output/csv/{composer}_piece_prog_percentages.csv",index=False)    
        prog_count_per_composer.to_csv(f"output/csv/{composer}_prog_count_per_composer.csv",index=False)    

    prog_count_all_composers = df

    print("\n--------------------")
    print("Execution Complete.")

    # get_progression_probs(composer, tsv_files)
    # # New: 21x21 root-change transition matrices
    # get_root_change_matrices(composer, tsv_files)
    # get_fine_progression_matrices(composer, tsv_files)

    





myself()