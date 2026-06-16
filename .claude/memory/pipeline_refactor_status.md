---
name: pipeline-refactor-status
description: "Current pipeline cleanup task: move messy blocks to helper functions, keep pipeline as high-level calls"
metadata: 
  node_type: memory
  type: project
  originSessionId: ec6565e1-cbe7-4142-94ec-dc19b29f9572
---

## Goal
Make `pipeline/pipeline.py` clean — mostly function calls, with implementation details in other files.

## What needs to be done

Three messy blocks in `pipeline/pipeline.py` need to be extracted into functions:

1. **Feature pipeline block (lines ~76–93)** — the features list + awkward `if f.__name__ == "add_n_gram"` check.
   → Becomes `process_piece(piece, system, n)` in `functions/per_piece_functions.py`
   → Returns `(df, piece_weighted)`
   → Needs `load_tsv` added to per_piece_functions.py imports: `from functions.utilities import frac_to_float, load_tsv`

2. **Per-piece CSV block (lines ~107–123)** — `itertools.product` dense CSV write per piece.
   → Becomes `write_piece_weighted_csv(composer, score, df, piece_weighted, n, output_dir)` in `functions/utilities.py`

3. **Global composer CSV block (lines ~138–155)** — `itertools.product` over global range, writes per-composer CSVs.
   → Becomes `write_composer_weighted_csvs(n_gram_weighted_dict, global_root_prog_vals, n)` in `functions/utilities.py`
   → Needs `import itertools` added to `utilities.py`

## Current pipeline state (as of this session)
- Per-composer analysis fully removed (no heatmaps, no composer CSVs)
- Dead variables kept by user preference: `n_gram_dict`, `all_progs_bigram_weighted_counts`
- `pieces_weighted_dir` now uses `output/{system}/n{n}/n_grams_weighted_pieces/` (n in path)
- `from config import composer_mid_life_dates` removed
- Features list includes `add_n_gram` and `add_n_gram_weighed` inline with awkward name-check

## Clean pipeline target

```python
for composer, pieces in pieces_grouped_by_composer.items():
    ...
    for piece in pieces:
        df, piece_weighted = process_piece(piece, system, n)
        ...
        if composer != "All" and piece_weighted:
            write_piece_weighted_csv(composer, piece.score, df, piece_weighted, n, pieces_weighted_dir)
    ...

write_composer_weighted_csvs(n_gram_weighted_dict, global_root_prog_vals, n)
```

**Why:** User wants pipeline readable as a high-level description; implementation details belong in helper files.
**How to apply:** Start with adding `load_tsv` to per_piece_functions.py imports, then add `process_piece`, then utilities functions, then rewrite pipeline.
