# pipeline/uri_pipeline.py
import pandas as pd
from pathlib import Path
from collections import defaultdict

from functions.fetch_scores import download_scores
from functions.per_piece_functions import (add_annotation_duration, 
                                           add_bigram_weight, 
                                           add_prog_weight, 
                                           add_root_diff, 
                                           add_root_progression_type_simple,
                                           convert_frac_cols_to_float, 
                                           drop_unnecessary_columns, 
                                           uri_system_filter,
                                           add_proper_empty_last_row,
                                           simple_prog_transition_counts)
from functions.per_composer_functions import (rootdiff_bigram_weight_matrix, 
                                              row_normalize_prog_weight_matrix,
                                              unconditional_joint_probs)
from functions.my_functions import (aggregate_prog_transition_unconditional, 
                                    aggregate_root_progs, 
                                    all_root_prog_transition_counts, 
                                    build_composer_prog_trans_df,
                                    build_progression_count_per_piece,
                                    composer_percentages_from_prog_counts,
                                    get_simple_prog_probs_row_normalized,
                                    get_uncond_probs,
                                    piece_progression_type_distribution,
                                    piece_prog_transition_unconditional,
                                    aggregate_progression_distribution,
                                    aggregate_prog_transition_unconditional,
                                    build_composer_prog_dist_df,
                                    build_composer_prog_trans_df)
from functions.utilities import (create_composer_file_lists, 
                                 load_tsv, 
                                 make_csv, 
                                 check_dirs,
                                 get_all_prog_categories_trimmed)
from functions.visualization import plot_heatmap
from config import (SIMPLE_PROGRESSION_CATEGORIES_URI,
                    SIMPLE_PROGRESSION_CATEGORIES_MARTIN,
                    ALL_PROGRESSION_VALUES_URI,
                    ALL_PROGRESSION_VALUES_MARTIN)
from config import REPOS
def run_pipeline(system):
    """
    
    """
    # Initializing Variables
    system=system.lower()
    if system == "martin":
        simple_categories = SIMPLE_PROGRESSION_CATEGORIES_MARTIN
        all_prog_values = ALL_PROGRESSION_VALUES_MARTIN
        print("\n--------------------\nRunning Martin's pipeline...")
    elif system == "uri":
        simple_categories = SIMPLE_PROGRESSION_CATEGORIES_URI
        all_prog_values = ALL_PROGRESSION_VALUES_URI
        print("\n--------------------\nRunning Uri's pipeline...")
    else:
        raise ValueError ("Invalid Pipeline System")
    check_dirs(system) # Checks that output folder exists, creates it if it doesnt
    download_scores() # Gets scores if theyre not already loaded in scores dir
    bach_tsv_files, mozart_tsv_files, beethoven_tsv_files, chopin_tsv_files, liszt_tsv_files, all_reviewed_tsv_files = create_composer_file_lists(REPOS) 
    # Dict with composer name and their corresponding tsv files list
    composer_dict = {
        "Bach": bach_tsv_files,
        # "Mozart": mozart_tsv_files,
        # "Beethoven": beethoven_tsv_files,
        # "Chopin": chopin_tsv_files,
        # "Liszt": liszt_tsv_files,
        # "All": all_reviewed_tsv_files,
        # "sanity": ["sanity.csv"]
    }
    print("\nRepos used:\n", REPOS, "\n")

    for composer, tsv_files in composer_dict.items():
        # Operations per Composer here
        print(f"Processing composer: {composer} with {len(tsv_files)} scores...")
        prog_count_per_piece_per_composer_rows, piece_prog_type_dist_rows, piece_prog_type_trans_rows = [],[],[]
        composer_root_diff_weight = defaultdict(float)  # {root_diff: total_prog_weight}
        global_simple_prog_counts = pd.DataFrame(0, index=list(simple_categories), columns=list(simple_categories), dtype=int)
        global_all_prog_counts = pd.DataFrame(0, index=list(all_prog_values), columns=list(all_prog_values), dtype=int)
        global_bigram_matrix = pd.DataFrame(0.0, index=all_prog_values, columns=all_prog_values)

        for piece_path in tsv_files:
            """ Operations per Piece here """
            score = Path(piece_path).stem.removesuffix("_reviewed")
            df = load_tsv(piece_path)
            if piece_path == "sanity.csv":
                from sanity import use_sanity
                df = use_sanity()
                
            features = [
                add_proper_empty_last_row,
                drop_unnecessary_columns,
                convert_frac_cols_to_float,
                add_root_diff, 
                add_root_progression_type_simple, 
                add_annotation_duration,
                add_prog_weight,
                add_bigram_weight
                ]
            if system == "uri":
                features.append(uri_system_filter)
            # Loop through each score's reviewed tsv file
            for f in features:
                # Add root difference,root progression types, and accumulate transition counts from all scores
                df = f(df)

            # Sanity functions
            # if tsv == "sanity.csv":
            #     df.to_csv("sanity_df.csv", index=False)
            # if score == "BWV1001_01_Adagio":
            #     df.to_csv("bach_df.csv", index=False)
            
            # Aggregate functions per piece
            piece_prog_type_dist = piece_progression_type_distribution(df, score)
            piece_prog_type_dist_rows.append( {"composer": composer, "piece": score, **piece_prog_type_dist.to_dict()} )
            piece_prog_type_trans = piece_prog_transition_unconditional(df, score)
            piece_prog_type_trans_rows.append({"composer": composer, "piece": score, **piece_prog_type_trans.to_dict()})
            prog_count_per_piece_per_composer_rows.append(build_progression_count_per_piece(Path(piece_path), df, composer, labels=simple_categories))
            simple_counts = simple_prog_transition_counts(df, categories=simple_categories)
            global_simple_prog_counts = global_simple_prog_counts.add(simple_counts,fill_value=0)
            global_all_prog_counts += all_root_prog_transition_counts(df, system)
            global_bigram_matrix += rootdiff_bigram_weight_matrix(df)  

            # 8/2/26
            # Uri's system
            piece_prog_weight_sum = (
                df.dropna(subset=["root_diff", "prog_weight"])
                    .assign(root_diff=lambda x: x["root_diff"].astype(int))
                    .groupby("root_diff")["prog_weight"]
                    .sum()
            )
            for root_diff, wsum in piece_prog_weight_sum.items():
                composer_root_diff_weight[ int(root_diff)] += float(wsum) # type: ignore

        prog_count_per_piece_per_composer_df= pd.DataFrame(prog_count_per_piece_per_composer_rows)
        # Stable column order
        prog_count_per_piece_per_composer_df = prog_count_per_piece_per_composer_df[["composer", "piece", "n"] + list(simple_categories) ]
        prog_percentage_per_composer = composer_percentages_from_prog_counts(prog_count_per_piece_per_composer_df)

        # SIMPLE PROGRESSION PROBS
        uncond_simple_trans_probs = get_uncond_probs(global_simple_prog_counts)

        # ALL PROGRESSION PROBS
        uncond_all_probs = aggregate_root_progs(global_all_prog_counts)
        print(uncond_all_probs.head())
        all_cats_trimmed = get_all_prog_categories_trimmed(global_all_prog_counts)

        # WEIGHTED ROOT DIFFERENCE TABLE
        composer_root_diff_weight_df = (
            pd.Series(composer_root_diff_weight, name="prog_weight_sum")
            .sort_index()
            .reset_index()
            .rename(columns={"index": "root_diff"})
        )
        # after all pieces:
        weight_joint = unconditional_joint_probs(global_bigram_matrix)
        composer_prog_type_dist_df = build_composer_prog_dist_df(piece_prog_type_dist_rows)
        composer_prog_type_trans_df = build_composer_prog_trans_df(piece_prog_type_trans_rows)

        # Outputs:
        # to .csv
        for df, name in [
            (composer_prog_type_dist_df, "composer_prog_type_dist_df"),
            (composer_prog_type_trans_df, "composer_prog_type_trans_df")]:
            make_csv(df, f"{composer}_{name}", system = system, path_modifier="piece")
            
        for df,name in [
            (prog_percentage_per_composer, "prog_percentage_per_composer"),
            (composer_root_diff_weight_df, "composer_root_diff_weight_df")]:
            make_csv(df, f"{composer}_{name}",system = system, path_modifier="composer") 

        # Output to graph imgs 
        plot_heatmap(system=system, composer=composer, graph_title = "SAW", filename=f"{composer}_SAW_{system}", transition_matrix=uncond_simple_trans_probs, categories=simple_categories)
        plot_heatmap(system=system, composer=composer, graph_title = "All Progs", filename=f"{composer}_ALL_{system}", transition_matrix=uncond_all_probs, categories=all_cats_trimmed )
        plot_heatmap(system=system, composer=composer, graph_title = "Weight of All Progs", filename=f"{composer}_ALL_WEIGHT_{system}", transition_matrix=weight_joint, categories=all_prog_values) 

    
    # Aggregate data per composer
    aggregate_composer_progs = aggregate_progression_distribution(composer_prog_type_dist_df)
    aggregate_composer_prog_transitions = aggregate_prog_transition_unconditional(composer_prog_type_trans_df)
    # Output to .csv
    for df, name in [
        (aggregate_composer_progs, "aggregate_composer_progs"),
        (aggregate_composer_prog_transitions, "aggregate_composer_prog_transitions")
            ]:
        make_csv(df, f"{name}",system = system, path_modifier="global")