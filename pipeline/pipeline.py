# pipeline/pipeline.py
import pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict, Counter
from functions.per_piece_functions import (
    add_annotation_duration, 
    add_bigram_prog_weight, 
    add_prog_weight, 
    add_root_diff, 
    add_root_progression_type_simple,
    convert_frac_cols_to_float, 
    drop_unnecessary_columns, 
    uri_system_filter,
    add_proper_empty_last_row,
    simple_prog_transition_counts,
    build_simple_progression_count_per_piece,
    count_weighted_root_diffs)
from functions.per_composer_functions import (
    composer_percentages_from_prog_counts,
    simple_prog_transition_per_piece,
    build_all_progs_weighted_matrix)
from functions.my_functions import (
    aggregate_prog_transition_unconditional,
    all_root_prog_transition_counts, 
    all_root_prog_counts,
    get_uncond_probs,
    piece_progression_type_distribution,
    aggregate_progression_distribution,
    aggregate_prog_transition_unconditional,
    build_composer_prog_dist_df)
from functions.utilities import (
    load_tsv, 
    make_csv, 
    check_dirs,
    pick_categories_based_on_system_type)
from functions.import_scores import build_piece_paths_list, group_by_composer
from functions.visualization import plot_heatmap, plot_stacked_bars
from config import composer_mid_life_dates
def run_pipeline(system):
    """
        Go through all reviewed tsv files.
        Build necessary features such as root_diff.
        Sum up all root progressions.
        Sum up all 2D root progressions.
        Calculate uncond probabilties.
        Create graphs and csv tables.
    """
    # ------------------------------------------
    # 1) Initialize system, categories, check dirs
    # ------------------------------------------
    system = system.lower()
    simple_categories = pick_categories_based_on_system_type(system)
    check_dirs(system) # Checks that output folder exists, creates it if it doesnt
    # ------------------------------------------
    # 2) Import scores, grouped by composer name
    # ------------------------------------------
    SCORES_ROOT = Path("scores")
    pieces_list = build_piece_paths_list(SCORES_ROOT)
    pieces_grouped_by_composer = group_by_composer(pieces_list)
    pieces_grouped_by_composer["All"] = pieces_list
    # ------------------------------------------
    # 3) Initialize global collectors
    # ------------------------------------------
    simple_prog_perct_with_composer_year_df = pd.DataFrame(columns=["composer"] + list(simple_categories) + ["n", "composer_mid_year"])
    all_progs_counter = []
    # ------------------------------------------
    # 4) Iterate over composers
    # ------------------------------------------
    for composer, pieces in pieces_grouped_by_composer.items():
        # ------------------------------------------
        # 5) Initialize per-composer collectors
        # ------------------------------------------
        print(f"Processing composer: {composer} with {len(pieces)} scores...")
        # per-composer accumulators
        simple_prog_count_per_composer_list, simple_piece_prog_type_dist_rows, piece_prog_type_trans_rows = [], [], []
        composer_root_diff_weight = defaultdict(float)  # {root_diff: total_prog_weight}
        simple_prog_bigram_counts = pd.DataFrame(0, index=list(simple_categories),columns=list(simple_categories), dtype=int)
        all_progs_unigram_counts = Counter() # unigram
        all_progs_bigram_weighted_counts = Counter() # bigram, weighted
        root_diff_set = set() # set of all root_diff values per composer
        # ------------------------------------------
        # 5) Iterate over pieces of each composer
        # ------------------------------------------
        for piece in pieces:
            # ------------------------------------------
            # Load piece, build features
            # ------------------------------------------
            df = load_tsv(piece.path)
            score = piece.score
            features = [
                add_proper_empty_last_row,
                drop_unnecessary_columns,
                convert_frac_cols_to_float,
                add_root_diff, 
                add_root_progression_type_simple, 
                add_annotation_duration,
                add_prog_weight,
                add_bigram_prog_weight
                ]
            if system == "uri":
                features.append(uri_system_filter)
            for f in features:
                # Add root difference,root progression types, and accumulate transition counts from all scores
                df = f(df)

            # ------------------------------------------
            # Collect info from each piece - simple and all progs, weights
            # ------------------------------------------

            # Update unique set of root_diff
            root_diff_set.update(df["root_diff"].dropna().astype(int).tolist())

            # piece_prog_type_dist = piece_progression_type_distribution(df, score,categories=simple_categories)
            # simple_piece_prog_type_dist_rows.append({"composer": composer, "piece": score, **piece_prog_type_dist.to_dict()} )
            # simple_prog_type_trans = simple_prog_transition_per_piece(df, score,categories=simple_categories)
            # piece_prog_type_trans_rows.append({"composer": composer, "piece": score, **simple_prog_type_trans.to_dict()})

            # ------------------------------------------
            # Simple progs (S,A,W,I)
            # ------------------------------------------
            simple_prog_count_per_composer_list.append(build_simple_progression_count_per_piece(Path(piece.path), df, composer, labels=simple_categories))
            simple_prog_bigram_count = simple_prog_transition_counts(df, categories=simple_categories)
            simple_prog_bigram_counts = simple_prog_bigram_count.add(simple_prog_bigram_counts,fill_value=0)
            # ------------------------------------------
            # All progs
            # ------------------------------------------
            all_progs_unigram_counts.update(all_root_prog_counts(df)) 
            all_progs_bigram_weighted_counts.update(count_weighted_root_diffs(df)) # Weighted
            # ------------------------------------------
            # Sum up weights of root progressions
            # ------------------------------------------
            piece_prog_weight_sum = (
                df.dropna(subset=["root_diff", "prog_weight"])
                .assign(root_diff=lambda x: x["root_diff"].astype(int))
                .groupby("root_diff")["prog_weight"]
                .sum()
            )
            # Assign weight to dict holder
            for root_diff, wsum in piece_prog_weight_sum.items():
                composer_root_diff_weight[ int(root_diff) ] += float(wsum) # type: ignore

        simple_prog_count_per_piece_per_composer_df= pd.DataFrame(simple_prog_count_per_composer_list)
        # Stable column order
        simple_prog_count_per_piece_per_composer_df = simple_prog_count_per_piece_per_composer_df[["composer", "piece", "n"] + list(simple_categories) ]
        simple_prog_percentage_per_composer = composer_percentages_from_prog_counts(simple_prog_count_per_piece_per_composer_df, categories=simple_categories)
        # DF with composer's year

        # Avoid counting "All" as a composer
        if composer != "All":
            tmp_row = {
                "composer": composer,
                "composer_mid_year": composer_mid_life_dates[composer],
            }
            # add progression counts as columns
            tmp_row.update(all_progs_unigram_counts)
            all_progs_counter.append(tmp_row)
    
        # SIMPLE PROGRESSION BIGRAM PROBS MATRIX
        simple_prog_bigram_probs = get_uncond_probs(simple_prog_bigram_counts)
                                                    
        # TABLE OF WEIGHTED DIFFERENCES OF ALL ROOT PROGS 

        root_diff_list = sorted(list(root_diff_set))
        composer_root_diff_weight_unigram_df = (
            pd.Series(composer_root_diff_weight, name="prog_weight_sum")
            .sort_index()
            .reset_index()
            .rename(columns={"index": "root_diff"})
        )
        # ALL PROGRESSION PROBS
        all_progs_weighted_matrix = build_all_progs_weighted_matrix(all_progs_bigram_weighted_counts,root_diff_list)
        # composer_prog_type_dist_df = build_composer_prog_dist_df(simple_piece_prog_type_dist_rows)
        # composer_prog_type_trans_df = pd.DataFrame(piece_prog_type_trans_rows).fillna(0.0)

        # Outputs:
        # CSVs
        # for df, name in [
        #     (composer_prog_type_dist_df, "composer_prog_type_dist_df"),
            # (composer_prog_type_trans_df, "composer_prog_type_trans_df")
            # ]:
            # make_csv(df, f"{composer}_{name}", system = system, path_modifier="piece") 
        for df,name in [
            # (simple_prog_percentage_per_composer, "simple_prog_percentage_per_composer"),
            (composer_root_diff_weight_unigram_df, "composer_root_diff_weight_unigram_df")
            ]:
            make_csv(df, f"{composer}_{name}",system = system, path_modifier="composer") 
        # Output to graph imgs 
        # plot_heatmap(system=system, composer=composer, graph_title = "SAW", filename=f"{composer}_SAW_{system}", transition_matrix=simple_prog_bigram_probs, categories=simple_categories)
        plot_heatmap(system=system, composer=composer, graph_title = "All Progs Weighted Values", filename=f"{composer}_ALL_WEIGHTED_{system}", transition_matrix=all_progs_weighted_matrix, categories=root_diff_list) 

    # ---------------------------------
    # Plotting all prog unigrams
    # ---------------------------------
    all_progs_count_df = pd.DataFrame(all_progs_counter).fillna(0)
    meta_cols = ["composer", "composer_mid_year"]
    # Identify progression columns
    prog_cols = [c for c in all_progs_count_df.columns if c not in meta_cols]

    # Make sure prog columns are numeric
    all_progs_count_df[prog_cols] = (
        all_progs_count_df[prog_cols]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
    )
    # Normalize each row to probabilities
    probs_df = all_progs_count_df.copy()
    row_sums = probs_df[prog_cols].sum(axis=1).replace(0, 1)
    probs_df[prog_cols] = probs_df[prog_cols].div(row_sums, axis=0)
    top_col_n_to_keep = 5
    # Keep only top 5 per row, melt directly into long format
    plot_df = (
        probs_df
        .set_index(meta_cols)[prog_cols]
        .apply(lambda row: row.where(row.isin(row.nlargest(top_col_n_to_keep))), axis=1)
        .stack()
        .reset_index()
        .rename(columns={"level_2": "root_prog", 0: "prob"})
    )

    plot_df["root_prog"] = plot_df["root_prog"].astype(str)
    # ------------------------------ 
    # Sort composers chronologically 
    # ------------------------------ 
    composer_order = ( 
    plot_df[["composer", "composer_mid_year"]] 
    .drop_duplicates() 
    .sort_values("composer_mid_year") 
    ) 
    ordered_composers = composer_order["composer"].tolist()

    # Pivot for stacked plotting
    stacked_df = (
        plot_df
        .pivot(index="composer", columns="root_prog", values="prob")
        .fillna(0)
        .loc[ordered_composers]
    )
    # PLOTTTING
    plot_stacked_bars(stacked_df, composer_order )

    # Aggregate data per composer
    # aggregate_composer_progs = aggregate_progression_distribution(composer_prog_type_dist_df,categories=simple_categories)
    # aggregate_composer_prog_transitions = aggregate_prog_transition_unconditional(composer_prog_type_trans_df)
    # Output to .csv
    # for df, name in [
    #     # (aggregate_composer_progs, "aggregate_composer_progs"),
    #     (aggregate_composer_prog_transitions, "aggregate_composer_prog_transitions") ]:
    #     make_csv(df, f"{name}",system = system, path_modifier="global")