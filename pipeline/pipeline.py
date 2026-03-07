# pipeline/pipeline.py
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
from functions.fetch_scores import download_scores
from functions.per_piece_functions import (
    add_annotation_duration, 
    add_bigram_weight, 
    add_prog_weight, 
    add_root_diff, 
    add_root_progression_type_simple,
    convert_frac_cols_to_float, 
    drop_unnecessary_columns, 
    uri_system_filter,
    add_proper_empty_last_row,
    simple_prog_transition_counts,
    build_progression_count_per_piece,
    count_weighted_root_diffs)
from functions.per_composer_functions import (
    rootdiff_bigram_weight_matrix,
    unconditional_joint_probs,
    composer_percentages_from_prog_counts,
    piece_prog_transition_unconditional,
    build_all_progs_weighted_matrix)
from functions.my_functions import (
    aggregate_prog_transition_unconditional,
    all_root_prog_transition_counts, 
    build_composer_prog_trans_df,
    get_uncond_probs,
    piece_progression_type_distribution,
    aggregate_progression_distribution,
    aggregate_prog_transition_unconditional,
    build_composer_prog_dist_df,
    build_composer_prog_trans_df)
from functions.utilities import (
    create_composer_file_lists, 
    load_tsv, 
    make_csv, 
    check_dirs,
    pick_categories_based_on_system_type,
    get_SAWINONE_PROG_CATEGORIES_trimmed)
from functions.import_scores import build_piece_index, group_by_composer
from functions.visualization import plot_heatmap
# from config import (REPOS)
def run_pipeline(system):
    system=system.lower()
    simple_categories = pick_categories_based_on_system_type(system)
    check_dirs(system) # Checks that output folder exists, creates it if it doesnt
    # download_scores() # Gets scores if theyre not already loaded in scores dir
    # bach_tsv_files, mozart_tsv_files, beethoven_tsv_files, chopin_tsv_files, liszt_tsv_files, all_reviewed_tsv_files = create_composer_file_lists(REPOS) 
    # composer_dict = {
    #     "Bach": bach_tsv_files,
    #     "Mozart": mozart_tsv_files,
    #     "Beethoven": beethoven_tsv_files,
    #     "Chopin": chopin_tsv_files,
    #     "Liszt": liszt_tsv_files,
    #     "All": all_reviewed_tsv_files
    # }
    scores_root = Path("scores")
    records = build_piece_index(scores_root)
    composer_groups = group_by_composer(records)
    composer_groups["All"] = records
    for composer, recs in composer_groups.items():
        print(f"Processing composer: {composer} with {len(recs)} scores...")
        # per-composer accumulators
        prog_count_per_piece_per_composer_rows, piece_prog_type_dist_rows, piece_prog_type_trans_rows = [], [], []
        prog_count_per_piece_per_composer_rows, piece_prog_type_dist_rows, piece_prog_type_trans_rows = [],[],[]
        composer_root_diff_weight = defaultdict(float)  # {root_diff: total_prog_weight}
        global_simple_prog_counts = pd.DataFrame(0, index=list(simple_categories), columns=list(simple_categories), dtype=int)
        #global_all_prog_counts = pd.DataFrame(0, index=list(all_prog_values), columns=list(all_prog_values), dtype=int)
        global_all_prog_counts = Counter()
        global_bigram_matrix_counts = Counter()
        #global_bigram_matrix = pd.DataFrame(0.0, index=all_prog_values, columns=all_prog_values)
        root_diff_set = set()

        for rec in recs:
            df = load_tsv(rec.path)
            score = rec.score  # same role as your old `Path(piece_path).stem...`
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
            root_diff_set.update(df["root_diff"].dropna().astype(int).tolist())
            # Aggregate functions per piece.
            piece_prog_type_dist = piece_progression_type_distribution(df, score,categories=simple_categories)
            piece_prog_type_dist_rows.append({"composer": composer, "piece": score, **piece_prog_type_dist.to_dict()} )
            piece_prog_type_trans = piece_prog_transition_unconditional(df, score,categories=simple_categories)
            piece_prog_type_trans_rows.append({"composer": composer, "piece": score, **piece_prog_type_trans.to_dict()})
            prog_count_per_piece_per_composer_rows.append(build_progression_count_per_piece(Path(rec.path), df, composer, labels=simple_categories))
            simple_counts = simple_prog_transition_counts(df, categories=simple_categories)
            global_simple_prog_counts = global_simple_prog_counts.add(simple_counts,fill_value=0)
            global_all_prog_counts.update(all_root_prog_transition_counts(df))
            global_bigram_matrix_counts.update(count_weighted_root_diffs(df))
            #global_all_prog_counts += all_root_prog_transition_counts(df, system)
            #global_bigram_matrix += rootdiff_bigram_weight_matrix(df)  

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
        prog_percentage_per_composer = composer_percentages_from_prog_counts(prog_count_per_piece_per_composer_df, categories=simple_categories)

        # SIMPLE PROGRESSION PROBS
        uncond_simple_trans_probs = get_uncond_probs(global_simple_prog_counts)
        # ALL PROGRESSION PROBS
        root_diff_list = sorted(list(root_diff_set))

        def build_all_counts_probs_matrix_from_counts(all_prog_counts_matrix):
            total = all_prog_counts_matrix.to_numpy().sum()
            # Trimming unused categories
            row_ct = all_prog_counts_matrix.sum(axis=1)
            col_ct = all_prog_counts_matrix.sum(axis=0)
            keep = (row_ct + col_ct) > 0
            counts_trim = all_prog_counts_matrix.loc[keep, keep]
            total = counts_trim.to_numpy().sum()
            all_prog_probs_matrix = (counts_trim / total) if total else counts_trim.astype(float)
            return all_prog_probs_matrix
        
        all_prog_counts_matrix = pd.DataFrame(0,index=root_diff_list,columns=root_diff_list,dtype=int)
        for (a, b), count in global_all_prog_counts.items():
            all_prog_counts_matrix.loc[a, b] = count
        
        all_prog_probs_matrix = build_all_counts_probs_matrix_from_counts(all_prog_counts_matrix)

        # uncond_all_probs = aggregate_root_progs(global_all_prog_counts)
        # all_cats_trimmed = get_SAWINONE_PROG_CATEGORIES_trimmed(global_all_prog_counts)

        # WEIGHTED ROOT DIFFERENCE TABLE
        composer_root_diff_weight_unigram_df = (
            pd.Series(composer_root_diff_weight, name="prog_weight_sum")
            .sort_index()
            .reset_index()
            .rename(columns={"index": "root_diff"})
        )
        # after all pieces:
        # weight_joint = unconditional_joint_probs(global_bigram_matrix)
        
        all_progs_weighted_matrix = build_all_progs_weighted_matrix(global_bigram_matrix_counts,root_diff_list)
        composer_prog_type_dist_df = build_composer_prog_dist_df(piece_prog_type_dist_rows)
        composer_prog_type_trans_df = build_composer_prog_trans_df(piece_prog_type_trans_rows)

        # Outputs:
        # to .csv
        for df, name in [
            (composer_prog_type_dist_df, "composer_prog_type_dist_df"),
            (composer_prog_type_trans_df, "composer_prog_type_trans_df")
            ]:
            make_csv(df, f"{composer}_{name}", system = system, path_modifier="piece") 
        for df,name in [
            (prog_percentage_per_composer, "prog_percentage_per_composer"),
            (composer_root_diff_weight_unigram_df, "composer_root_diff_weight_unigram_df")
            ]:
            make_csv(df, f"{composer}_{name}",system = system, path_modifier="composer") 
        # Output to graph imgs 
        plot_heatmap(system=system, composer=composer, graph_title = "SAW", filename=f"{composer}_SAW_{system}", transition_matrix=uncond_simple_trans_probs, categories=simple_categories)
        plot_heatmap(system=system, composer=composer, graph_title = "All Progs Unweighted Values", filename=f"{composer}_ALL_{system}", transition_matrix=all_prog_probs_matrix, categories=root_diff_list )
        plot_heatmap(system=system, composer=composer, graph_title = "All Progs Weighted Values", filename=f"{composer}_ALL_WEIGHTED_{system}", transition_matrix=all_progs_weighted_matrix, categories=root_diff_list) 

    # Aggregate data per composer
    aggregate_composer_progs = aggregate_progression_distribution(composer_prog_type_dist_df,categories=simple_categories)
    aggregate_composer_prog_transitions = aggregate_prog_transition_unconditional(composer_prog_type_trans_df)
    # Output to .csv
    for df, name in [
        (aggregate_composer_progs, "aggregate_composer_progs"),
        (aggregate_composer_prog_transitions, "aggregate_composer_prog_transitions")
        ]:
        make_csv(df, f"{name}",system = system, path_modifier="global")




    # for composer, tsv_files in composer_dict.items():
    #     # Operations per Composer here
    #     print(f"Processing composer: {composer} with {len(tsv_files)} scores...")
    #     prog_count_per_piece_per_composer_rows, piece_prog_type_dist_rows, piece_prog_type_trans_rows = [],[],[]
    #     composer_root_diff_weight = defaultdict(float)  # {root_diff: total_prog_weight}
    #     global_simple_prog_counts = pd.DataFrame(0, index=list(simple_categories), columns=list(simple_categories), dtype=int)
    #     #global_all_prog_counts = pd.DataFrame(0, index=list(all_prog_values), columns=list(all_prog_values), dtype=int)
    #     global_all_prog_counts = Counter()
    #     global_bigram_matrix_counts = Counter()
    #     #global_bigram_matrix = pd.DataFrame(0.0, index=all_prog_values, columns=all_prog_values)
    #     root_diff_set = set()

    #     for piece_path in tsv_files:
    #         """ Operations per Piece here """
    #         score = Path(piece_path).stem.removesuffix("_reviewed")
    #         df = load_tsv(piece_path)
    #         features = [
    #             add_proper_empty_last_row,
    #             drop_unnecessary_columns,
    #             convert_frac_cols_to_float,
    #             add_root_diff, 
    #             add_root_progression_type_simple, 
    #             add_annotation_duration,
    #             add_prog_weight,
    #             add_bigram_weight
    #             ]
    #         if system == "uri":
    #             features.append(uri_system_filter)
    #         # Loop through each score's reviewed tsv file
    #         for f in features:
    #             # Add root difference,root progression types, and accumulate transition counts from all scores
    #             df = f(df)
    #         root_diff_set.update(df["root_diff"].dropna().astype(int).tolist())
    #         # Aggregate functions per piece.
    #         piece_prog_type_dist = piece_progression_type_distribution(df, score,categories=simple_categories)
    #         piece_prog_type_dist_rows.append({"composer": composer, "piece": score, **piece_prog_type_dist.to_dict()} )
    #         piece_prog_type_trans = piece_prog_transition_unconditional(df, score,categories=simple_categories)
    #         piece_prog_type_trans_rows.append({"composer": composer, "piece": score, **piece_prog_type_trans.to_dict()})
    #         prog_count_per_piece_per_composer_rows.append(build_progression_count_per_piece(Path(piece_path), df, composer, labels=simple_categories))
    #         simple_counts = simple_prog_transition_counts(df, categories=simple_categories)
    #         global_simple_prog_counts = global_simple_prog_counts.add(simple_counts,fill_value=0)
    #         global_all_prog_counts.update(all_root_prog_transition_counts(df))
    #         global_bigram_matrix_counts.update(count_weighted_root_diffs(df))
    #         #global_all_prog_counts += all_root_prog_transition_counts(df, system)
    #         #global_bigram_matrix += rootdiff_bigram_weight_matrix(df)  

    #         # 8/2/26
    #         # Uri's system
    #         piece_prog_weight_sum = (
    #             df.dropna(subset=["root_diff", "prog_weight"])
    #                 .assign(root_diff=lambda x: x["root_diff"].astype(int))
    #                 .groupby("root_diff")["prog_weight"]
    #                 .sum()
    #         )
    #         for root_diff, wsum in piece_prog_weight_sum.items():
    #             composer_root_diff_weight[ int(root_diff)] += float(wsum) # type: ignore
    #     prog_count_per_piece_per_composer_df= pd.DataFrame(prog_count_per_piece_per_composer_rows)
    #     # Stable column order
    #     prog_count_per_piece_per_composer_df = prog_count_per_piece_per_composer_df[["composer", "piece", "n"] + list(simple_categories) ]
    #     prog_percentage_per_composer = composer_percentages_from_prog_counts(prog_count_per_piece_per_composer_df, categories=simple_categories)

    #     # SIMPLE PROGRESSION PROBS
    #     uncond_simple_trans_probs = get_uncond_probs(global_simple_prog_counts)
    #     # ALL PROGRESSION PROBS
    #     root_diff_list = sorted(list(root_diff_set))

    #     def build_all_counts_probs_matrix_from_counts(all_prog_counts_matrix):
    #         total = all_prog_counts_matrix.to_numpy().sum()
    #         # Trimming unused categories
    #         row_ct = all_prog_counts_matrix.sum(axis=1)
    #         col_ct = all_prog_counts_matrix.sum(axis=0)
    #         keep = (row_ct + col_ct) > 0
    #         counts_trim = all_prog_counts_matrix.loc[keep, keep]
    #         total = counts_trim.to_numpy().sum()
    #         all_prog_probs_matrix = (counts_trim / total) if total else counts_trim.astype(float)
    #         return all_prog_probs_matrix
        
    #     all_prog_counts_matrix = pd.DataFrame(0,index=root_diff_list,columns=root_diff_list,dtype=int)
    #     for (a, b), count in global_all_prog_counts.items():
    #         all_prog_counts_matrix.loc[a, b] = count
        
    #     all_prog_probs_matrix = build_all_counts_probs_matrix_from_counts(all_prog_counts_matrix)

    #     # uncond_all_probs = aggregate_root_progs(global_all_prog_counts)
    #     # all_cats_trimmed = get_SAWINONE_PROG_CATEGORIES_trimmed(global_all_prog_counts)

    #     # WEIGHTED ROOT DIFFERENCE TABLE
    #     composer_root_diff_weight_unigram_df = (
    #         pd.Series(composer_root_diff_weight, name="prog_weight_sum")
    #         .sort_index()
    #         .reset_index()
    #         .rename(columns={"index": "root_diff"})
    #     )
    #     # after all pieces:
    #     # weight_joint = unconditional_joint_probs(global_bigram_matrix)
        
    #     all_progs_weighted_matrix = build_all_progs_weighted_matrix(global_bigram_matrix_counts,root_diff_list)
    #     composer_prog_type_dist_df = build_composer_prog_dist_df(piece_prog_type_dist_rows)
    #     composer_prog_type_trans_df = build_composer_prog_trans_df(piece_prog_type_trans_rows)

    #     # Outputs:
    #     # to .csv
    #     for df, name in [
    #         (composer_prog_type_dist_df, "composer_prog_type_dist_df"),
    #         (composer_prog_type_trans_df, "composer_prog_type_trans_df")
    #         ]:
    #         make_csv(df, f"{composer}_{name}", system = system, path_modifier="piece") 
    #     for df,name in [
    #         (prog_percentage_per_composer, "prog_percentage_per_composer"),
    #         (composer_root_diff_weight_unigram_df, "composer_root_diff_weight_unigram_df")
    #         ]:
    #         make_csv(df, f"{composer}_{name}",system = system, path_modifier="composer") 
    #     # Output to graph imgs 
    #     plot_heatmap(system=system, composer=composer, graph_title = "SAW", filename=f"{composer}_SAW_{system}", transition_matrix=uncond_simple_trans_probs, categories=simple_categories)
    #     plot_heatmap(system=system, composer=composer, graph_title = "All Progs Unweighted Values", filename=f"{composer}_ALL_{system}", transition_matrix=all_prog_probs_matrix, categories=root_diff_list )
    #     plot_heatmap(system=system, composer=composer, graph_title = "All Progs Weighted Values", filename=f"{composer}_ALL_WEIGHTED_{system}", transition_matrix=all_progs_weighted_matrix, categories=root_diff_list) 

    # # Aggregate data per composer
    # aggregate_composer_progs = aggregate_progression_distribution(composer_prog_type_dist_df,categories=simple_categories)
    # aggregate_composer_prog_transitions = aggregate_prog_transition_unconditional(composer_prog_type_trans_df)
    # # Output to .csv
    # for df, name in [
    #     (aggregate_composer_progs, "aggregate_composer_progs"),
    #     (aggregate_composer_prog_transitions, "aggregate_composer_prog_transitions")
    #     ]:
    #     make_csv(df, f"{name}",system = system, path_modifier="global")