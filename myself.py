import pandas as pd
from pathlib import Path

from config import (ALL_PROG_CATEGORIES,
                    SIMPLE_PROGRESSION_CATEGORIES_URI,
                    SIMPLE_PROGRESSION_CATEGORIES_MARTIN,
                    FINE_PROGRESSION_CATEGORIES_URI,
                    FINE_PROGRESSION_CATEGORIES_MARTIN,
                    ALL_PROGRESSION_VALUES_URI,
                    ALL_PROGRESSION_VALUES_MARTIN,
                    REPOS
                    )
from fetch_scores import download_reviewed_folder
from utilities import create_composer_file_lists, get_diff_categories_trimmed, load_tsv, make_csv, check_dirs
from my_functions import (aggregate_prog_transition_unconditional, 
                          aggregate_root_progs, 
                          all_root_prog_transition_counts, 
                          build_composer_prog_trans_df,
                          build_progression_count_per_piece,
                          composer_percentages_from_piece_counts, fine_progression_transition_counts, get_fine_progression_matrix,
                          piece_percentages_from_counts,
                          row_normalized_progression_probs,
                          get_cond_probs,
                          get_uncond_probs,
                          piece_progression_type_distribution,
                          piece_prog_transition_unconditional,
                          aggregate_progression_distribution,
                          aggregate_prog_transition_unconditional,
                          build_composer_prog_dist_df,
                          build_composer_prog_trans_df)
from per_piece_functions import add_root_diff, add_root_progression_type_simple, add_root_progression_type_fine
from visualization import save_heatmaps

def myself():
    """
        1. Get tsv files in a list of paths.
        2. Run a loop for each composer and create a DF for each composer.
        3. On these DFs, perform the analysis, create features.
    """
    # Check that output directories exist, if not - create them
    check_dirs()

    for repo in REPOS:
        download_reviewed_folder(repo)

    all_reviewed_tsv_files, bach_tsv_files, mozart_tsv_files, beethoven_tsv_files, chopin_tsv_files, liszt_tsv_files = create_composer_file_lists(REPOS) 
    # Dict with composer name and their corresponding tsv files list
    composer_dict = {
        "Bach": bach_tsv_files,
        "Mozart": mozart_tsv_files,
        # "Beethoven": beethoven_tsv_files,
        # "Chopin": chopin_tsv_files,
        # "Liszt": liszt_tsv_files,
        # "All": all_reviewed_tsv_files
    }

    for composer, tsv_files in composer_dict.items():
        """ Operations per Composer here"""
        print(f"Processing composer: {composer} with {len(tsv_files)} scores...")
        prog_count_per_piece_per_composer, piece_prog_type_dist_rows, piece_prog_type_trans_rows = [], [], []
        global_simple_prog_counts = pd.DataFrame(0, index=list(SIMPLE_PROGRESSION_CATEGORIES_URI), columns=list(SIMPLE_PROGRESSION_CATEGORIES_URI), dtype=int)
        global_fine_prog_counts = pd.DataFrame(0, index=list(FINE_PROGRESSION_CATEGORIES_URI), columns=list(FINE_PROGRESSION_CATEGORIES_URI), dtype=int)
        global_all_prog_counts = pd.DataFrame(0, index=list(ALL_PROGRESSION_VALUES_URI), columns=list(ALL_PROGRESSION_VALUES_URI), dtype=int)
        
        for tsv in tsv_files:
            score = Path(tsv).stem.removesuffix("_reviewed")
            df = load_tsv(tsv)
            """ Operations per Piece here """
            # Loop through each score's reviewed tsv file
            for funcs in [add_root_diff, add_root_progression_type_simple, add_root_progression_type_fine]:
                # Add root difference,root progression types, and accumulate transition counts from all scores
                df = funcs(df)
            piece_prog_type_dist = piece_progression_type_distribution(df, score)
            piece_prog_type_dist_rows.append( {"composer": composer, "piece": score, **piece_prog_type_dist.to_dict()} )
            piece_prog_type_trans = piece_prog_transition_unconditional(df, score)
            piece_prog_type_trans_rows.append({"composer": composer, "piece": score, **piece_prog_type_trans.to_dict()})
            prog_count_per_piece_per_composer.append(build_progression_count_per_piece(Path(tsv), df, composer))
            global_simple_prog_counts += row_normalized_progression_probs(df,categories=SIMPLE_PROGRESSION_CATEGORIES_URI)
            global_fine_prog_counts += fine_progression_transition_counts(df)
            global_all_prog_counts += all_root_prog_transition_counts(df)

            # 7/2/26
            # Uri's system

            # -----------------------------
            ### End of operations per Piece
        
        prog_count_per_composer = pd.DataFrame(prog_count_per_piece_per_composer)
        # Stable column order
        prog_count_per_composer = prog_count_per_composer[["composer", "piece", "n"] + list(SIMPLE_PROGRESSION_CATEGORIES_URI) ]
        composer_prog_percentages = piece_percentages_from_counts(prog_count_per_composer)
        prog_percentage_per_composer = composer_percentages_from_piece_counts(prog_count_per_composer)
        # SIMPLE PROGRESSION PROBS
        cond_probs = get_cond_probs(global_simple_prog_counts)
        uncond_probs = get_uncond_probs(global_simple_prog_counts)
        # FINE PROGRESSION PROBS
        cond_probs_fine_uri, uncond_probs_fine_uri = get_fine_progression_matrix(composer, global_fine_prog_counts, categories=FINE_PROGRESSION_CATEGORIES_URI)
        cond_probs_fine_martin, uncond_probs_fine_martin = get_fine_progression_matrix(composer, global_fine_prog_counts, categories=FINE_PROGRESSION_CATEGORIES_MARTIN)

        # ALL PROGRESSION PROBS
        cond_all_probs, uncond_all_probs = aggregate_root_progs(composer, global_all_prog_counts)
        diff_cats_trim = get_diff_categories_trimmed(global_all_prog_counts)

        save_heatmaps(composer, cond_probs, uncond_probs, cond_probs_fine_uri, uncond_probs_fine_uri, cond_all_probs, uncond_all_probs, diff_cats_trim)
        #save_heatmaps(composer, cond_probs, uncond_probs, cond_probs_fine_martin, uncond_probs_fine_martin, cond_all_probs, uncond_all_probs, diff_cats_trim)
        # Output to .csv
        for df,name in [(prog_percentage_per_composer, "piece_counts"),
            (composer_prog_percentages, "composer_prog_percentages"),
            (prog_count_per_composer, "prog_count_per_composer")]:
            make_csv(df, f"{composer}_{name}")    
    # End of both loops
    composer_prog_type_dist_df = build_composer_prog_dist_df(piece_prog_type_dist_rows)
    composer_prog_type_trans_df = build_composer_prog_trans_df(piece_prog_type_trans_rows)
    aggregate_composer_progs = aggregate_progression_distribution(composer_prog_type_dist_df)
    aggregate_composer_prog_transitions = aggregate_prog_transition_unconditional(composer_prog_type_trans_df)

    # Output to .csv
    for df, name in [
        (composer_prog_type_dist_df, "composer_prog_type_dist_df"),
        (composer_prog_type_trans_df, "composer_prog_type_trans_df"),
        (aggregate_composer_progs, "aggregate_composer_progs"),
        (aggregate_composer_prog_transitions, "aggregate_composer_prog_transitions")
            ]:
        make_csv(df, f"{name}")

if __name__ == "__main__":
    print("Starting execution of myself.py...")
    print("\n--------------------")
    myself()
    print("\n--------------------")
    print("Execution Complete.")