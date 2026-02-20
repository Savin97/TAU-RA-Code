# pipeline/uri_pipeline.py
import pandas as pd
from pathlib import Path
from collections import defaultdict

from config import (ALL_PROG_CATEGORIES,
                    SIMPLE_PROGRESSION_CATEGORIES_URI,
                    ALL_PROGRESSION_VALUES_URI,
                    REPOS)
from functions.fetch_scores import download_scores
from functions.per_composer_functions import (rootdiff_bigram_weight_matrix, 
                                              row_normalize_prog_weight_matrix,
                                              unconditional_joint_probs)
from functions.utilities import (create_composer_file_lists, 
                                 load_tsv, 
                                 make_csv, 
                                 check_dirs,
                                 get_diff_categories_trimmed)
from functions.my_functions import (aggregate_prog_transition_unconditional, 
                                    aggregate_root_progs, 
                                    all_root_prog_transition_counts, 
                                    build_composer_prog_trans_df,
                                    build_progression_count_per_piece,
                                    composer_percentages_from_piece_counts,
                                    get_simple_prog_probs_row_normalized,
                                    get_uncond_probs,
                                    piece_progression_type_distribution,
                                    piece_prog_transition_unconditional,
                                    aggregate_progression_distribution,
                                    aggregate_prog_transition_unconditional,
                                    build_composer_prog_dist_df,
                                    build_composer_prog_trans_df)
from functions.per_piece_functions import (add_annotation_duration, 
                                           add_bigram_weight, 
                                           add_prog_weight, 
                                           add_root_diff, 
                                           add_root_progression_type_simple,
                                           convert_frac_cols_to_float, 
                                           drop_unnecessary_columns, 
                                           uri_system_filter,
                                           add_proper_empty_last_row)
from functions.visualization import save_heatmaps

def run_uri_pipeline():
    check_dirs() # Checks that output folder exists, creates it if it doesnt
    download_scores() # Gets scores if theyre not already loaded in scores dir
    all_reviewed_tsv_files, bach_tsv_files, mozart_tsv_files, beethoven_tsv_files, chopin_tsv_files, liszt_tsv_files = create_composer_file_lists(REPOS) 
    
    # Dict with composer name and their corresponding tsv files list
    composer_dict = {
        "Bach": bach_tsv_files,
        # "Mozart": mozart_tsv_files,
        # "Beethoven": beethoven_tsv_files,
        # "Chopin": chopin_tsv_files,
        # "Liszt": liszt_tsv_files,
        # "All": all_reviewed_tsv_files,
        "sanity": ["sanity.csv"]
    }

    for composer, tsv_files in composer_dict.items():
        # Operations per Composer here
        print(f"Processing composer: {composer} with {len(tsv_files)} scores...")
        prog_count_per_piece_per_composer = piece_prog_type_dist_rows = piece_prog_type_trans_rows = []
        composer_root_diff_weight = defaultdict(float)  # {root_diff: total_prog_weight}

        global_simple_prog_counts = pd.DataFrame(0, index=list(SIMPLE_PROGRESSION_CATEGORIES_URI), columns=list(SIMPLE_PROGRESSION_CATEGORIES_URI), dtype=int)
        global_all_prog_counts = pd.DataFrame(0, index=list(ALL_PROGRESSION_VALUES_URI), columns=list(ALL_PROGRESSION_VALUES_URI), dtype=int)
        global_bigram_matrix = pd.DataFrame(0.0, index=ALL_PROGRESSION_VALUES_URI, columns=ALL_PROGRESSION_VALUES_URI)
        
        for tsv in tsv_files:
            """ Operations per Piece here """
            score = Path(tsv).stem.removesuffix("_reviewed")
            if tsv == "sanity.csv":
                from sanity import use_sanity
                df = use_sanity()
            else:
                df = load_tsv(tsv)
            features = [
                add_proper_empty_last_row,
                drop_unnecessary_columns,
                convert_frac_cols_to_float,
                add_root_diff, 
                add_root_progression_type_simple, 
                add_annotation_duration,
                add_prog_weight,
                add_bigram_weight,
                # uri_system_filter
                ]
            # Loop through each score's reviewed tsv file
            for f in features:
                # Add root difference,root progression types, and accumulate transition counts from all scores
                df = f(df)
            # Sanity functions
            df.to_csv("sanity_df.csv", index=False)
            if score == "BWV1001_01_Adagio":
                df.to_csv("bach_df.csv", index=False)
            # Aggregate functions per piece
            piece_prog_type_dist = piece_progression_type_distribution(df, score)
            piece_prog_type_dist_rows.append( {"composer": composer, "piece": score, **piece_prog_type_dist.to_dict()} )
            piece_prog_type_trans = piece_prog_transition_unconditional(df, score)
            piece_prog_type_trans_rows.append({"composer": composer, "piece": score, **piece_prog_type_trans.to_dict()})
            prog_count_per_piece_per_composer.append(build_progression_count_per_piece(Path(tsv), df, composer))

            def simple_transition_counts(df, categories=SIMPLE_PROGRESSION_CATEGORIES_URI, col="progression_type_simple"):
                """
                    Return a |cats|x|cats| DataFrame of transition COUNTS:
                    rows = current, cols = next.
                """
                s = df[col]
                cur = s
                nxt = s.shift(-1)

                # keep only transitions where both sides are valid categories
                mask = cur.isin(categories) & nxt.isin(categories)
                cur = cur[mask]
                nxt = nxt[mask]

                mat = pd.crosstab(cur, nxt)

                # force exact grid + order
                mat = mat.reindex(index=list(categories), columns=list(categories), fill_value=0).astype(int)
                return mat
            
            simple_counts = simple_transition_counts(df, categories=SIMPLE_PROGRESSION_CATEGORIES_URI)
            global_simple_prog_counts = global_simple_prog_counts.add(simple_counts,fill_value=0)
            global_all_prog_counts += all_root_prog_transition_counts(df)
            global_bigram_matrix += rootdiff_bigram_weight_matrix(df)  

            # 8/2/26
            # Uri's system
            piece_sums = (
                df.dropna(subset=["root_diff", "prog_weight"])
                    .assign(root_diff=lambda x: x["root_diff"].astype(int))
                    .groupby("root_diff")["prog_weight"]
                    .sum()
            )
            for root_diff, wsum in piece_sums.items():
                composer_root_diff_weight[ int(root_diff)] += float(wsum) # type: ignore

        prog_count_per_piece= pd.DataFrame(prog_count_per_piece_per_composer)
        # Stable column order
        prog_count_per_piece = prog_count_per_piece[["composer", "piece", "n"] + list(SIMPLE_PROGRESSION_CATEGORIES_URI) ]
        
        prog_percentage_per_composer = composer_percentages_from_piece_counts(prog_count_per_piece)
        # SIMPLE PROGRESSION PROBS
        uncond_probs = get_uncond_probs(global_simple_prog_counts)
        # ALL PROGRESSION PROBS
        uncond_all_probs = aggregate_root_progs(composer, global_all_prog_counts)
        diff_cats_trim = get_diff_categories_trimmed(global_all_prog_counts)
        # WEIGHTED ROOT DIFFERENCE TABLE
        composer_root_diff_weight_df = (
            pd.Series(composer_root_diff_weight, name="prog_weight_sum")
            .sort_index()
            .reset_index()
            .rename(columns={"index": "root_diff"})
        )
        # after all pieces:
        weight_joint = unconditional_joint_probs(global_bigram_matrix)
        save_heatmaps(composer, uncond_probs, uncond_all_probs, diff_cats_trim, weight_joint)
        composer_prog_type_dist_df = build_composer_prog_dist_df(piece_prog_type_dist_rows)
        composer_prog_type_trans_df = build_composer_prog_trans_df(piece_prog_type_trans_rows)
        
        # Output to .csv
        for df, name in [
            (composer_prog_type_dist_df, "composer_prog_type_dist_df"),
            (composer_prog_type_trans_df, "composer_prog_type_trans_df")]:
            make_csv(df, f"{composer}_{name}", "piece")
            
        for df,name in [
            (prog_percentage_per_composer, "prog_percentage_per_composer"),
            (composer_root_diff_weight_df, "composer_root_diff_weight_df")]:
            make_csv(df, f"{composer}_{name}", "composer")    
    
    # Aggregate data per composer
    aggregate_composer_progs = aggregate_progression_distribution(composer_prog_type_dist_df)
    aggregate_composer_prog_transitions = aggregate_prog_transition_unconditional(composer_prog_type_trans_df)
    # Output to .csv
    for df, name in [
        (aggregate_composer_progs, "aggregate_composer_progs"),
        (aggregate_composer_prog_transitions, "aggregate_composer_prog_transitions")
            ]:
        make_csv(df, f"{name}", "global")