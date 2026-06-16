# pipeline/pipeline.py
"""
    Go through all reviewed tsv files.
    Build necessary features such as root_prog.
    Sum up all root progressions.
    Sum up all 2D root progressions.
    Calculate uncond probabilties.
    Create graphs and csv tables.
"""
import itertools
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
from functions.per_piece_functions import (
    add_annotation_duration,
    add_n_gram,
    add_n_gram_weighed,
    get_weighted_ngrams,
    add_bigram_prog_weight,
    add_prog_weight,
    add_root_prog,
    convert_frac_cols_to_float,
    drop_unnecessary_columns,
    uri_system_filter,
    add_proper_empty_last_row,
    count_weighted_root_progs)

from functions.utilities import (
    load_tsv,
    check_dirs)
from functions.import_scores import build_piece_paths_list, group_by_composer

def run_pipeline(system, n):
    # ------------------------------------------
    # 1) Initialize system, categories, check dirs
    # ------------------------------------------
    system = system.lower()
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
    n_gram_dict = {}
    n_gram_weighted_dict = {}
    global_root_prog_vals = set()
    pieces_weighted_dir = Path(f"output/{system}/n{n}/n_grams_weighted_pieces/")
    pieces_weighted_dir.mkdir(parents=True, exist_ok=True)
    # ------------------------------------------
    # 4) Iterate over composers
    # ------------------------------------------
    for composer, pieces in pieces_grouped_by_composer.items():
        # ------------------------------------------
        # 5) Initialize per-composer collectors
        # ------------------------------------------
        print(f"Processing composer: {composer} with {len(pieces)} scores...")
        # Per-composer accumulators
        all_progs_bigram_weighted_counts = Counter() # bigram, weighted
        n_gram_counter = Counter()
        n_gram_weighted_counter = defaultdict(float)
        # ------------------------------------------
        # 6) Iterate over pieces of each composer
        # ------------------------------------------

        for piece in pieces:
            # ------------------------------------------
            # Load piece, build features
            # ------------------------------------------
            df = load_tsv(piece.path)
            score = piece.score # score name
            features = [
                add_proper_empty_last_row,
                drop_unnecessary_columns,
                add_root_prog,
                convert_frac_cols_to_float,
                add_annotation_duration,
                add_prog_weight,
                add_bigram_prog_weight,
                add_n_gram,
                add_n_gram_weighed
                ]
            if system == "uri":
                features.append(uri_system_filter)
            for f in features:
                if f.__name__ == "add_n_gram" or f.__name__ == "add_n_gram_weighed":
                    df = f(df,n)
                else:
                    df = f(df)
            # ------------------------------------------
            # Collect info from each piece - all progs, weights
            # ------------------------------------------
            # Update unique set of root_prog
            piece_root_prog_vals = df["root_prog"].dropna().astype(int).tolist()
            global_root_prog_vals.update(piece_root_prog_vals)
            all_progs_bigram_weighted_counts.update(count_weighted_root_progs(df)) # Weighted

            n_gram_counter.update(df[f"{n}-gram_progs"])
            piece_weighted = get_weighted_ngrams(df, n)
            for gram, w in piece_weighted.items():
                n_gram_weighted_counter[gram] += w

            #------------------------------------
            # Write per-piece weighted n-gram CSV
            #------------------------------------
            if composer != "All" and piece_weighted:
                rp_vals = df["root_prog"].dropna().astype(int)
                rp_min, rp_max = int(rp_vals.min()), int(rp_vals.max())

                all_keys = list(itertools.product(range(rp_min, rp_max + 1), repeat=n))
                pw_values = [piece_weighted.get(k, 0.0) for k in all_keys]

                pd.DataFrame({
                    "vector": all_keys,
                    "weight": [round(v, 3) for v in pw_values]
                }).to_csv(
                    pieces_weighted_dir / f"{composer}_{score}.csv",
                    index=False
                )
            # ------------------------------------------
            # END OF PIECES LOOP
            # ------------------------------------------

        # ------------------------------------------
        # COMPOSERS LOOP
        # ------------------------------------------
        # n-grams
        n_gram_dict[composer] = n_gram_counter
        n_gram_weighted_dict[composer] = dict(n_gram_weighted_counter)
        # ------------------------------------------
        # END OF COMPOSERS LOOP
        # ------------------------------------------

    # ---------------------------------
    # Weighted n-grams output
    # ---------------------------------
    rp_min = min(global_root_prog_vals)
    rp_max = max(global_root_prog_vals)
    all_keys = list(itertools.product(range(rp_min, rp_max + 1), repeat=n))
    weighted_dir = Path(f"output/{system}/n{n}/n_grams_weighted")
    weighted_dir.mkdir(exist_ok=True)
    for composer, weighted_counts in n_gram_weighted_dict.items():
        values = [weighted_counts.get(k, 0.0) for k in all_keys]
        pd.DataFrame({
            "vector": all_keys,
            "weight": [round(v, 3) for v in values]
        }).to_csv(
            weighted_dir / f"{composer}.csv",
            index=False
        )
    print(f"Created weighted n-gram CSV files in '{weighted_dir}/'.")
