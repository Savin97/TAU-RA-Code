# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Memory

Session notes, task status, and ongoing context are stored in `.claude/memory/`. Read `.claude/memory/MEMORY.md` for the index at the start of each session.

## What this project does

This is a music theory research tool (Tel Aviv University) that analyzes harmonic root progressions across a corpus of classical music scores. It ingests reviewed TSV annotation files (one per piece), computes root-progression statistics, and outputs heatmaps and stacked-bar charts along with CSV summary tables.

## Running the pipeline

```bash
python main.py
```

The two tuneable parameters are in `main.py`:
- `system`: `"final"` (includes identical-root progressions, category `I`) or `"uri"` (excludes them)
- `n`: n-gram length (e.g. `3` for trigrams)

Output lands in `output/<system>/img/` (PNG graphs) and `output/<system>/csv/` (CSVs), plus a top-level `n-grams.txt`.

## Dependencies

```bash
pip install -r requirements.txt
```

Uses a local `.venv`. No test suite or linter is configured.

## Architecture

The pipeline runs in `pipeline/pipeline.py → run_pipeline()`. The flow is:

1. **Import** – `functions/import_scores.py` walks `scores/<repo>/reviewed/*.tsv`, infers composer from the repo folder name, and returns a list of `PieceRecord` dataclasses.
2. **Per-piece feature engineering** – `functions/per_piece_functions.py` applies a list of transform functions to each piece's DataFrame in sequence:
   - `add_root_prog`: semitone diff between consecutive root values (`root_prog = root.diff()`)
   - `add_annotation_duration` / `add_prog_weight` / `add_bigram_prog_weight`: duration-based weights
   - `add_n_gram` / `add_n_gram_weighed`: sliding window over `root_prog`
   - `uri_system_filter`: removes repeated-root rows (only active when `system="uri"`)
3. **Per-composer aggregation** – `functions/per_composer_functions.py` accumulates weighted bigram matrices across pieces.
4. **Global aggregation** – `functions/my_functions.py` collects unigram counts per composer and builds the cross-composer stacked-bar data.
5. **Output** – `functions/visualization.py` produces heatmaps (per-composer weighted transition matrix) and a chronological stacked-bar chart. `functions/utilities.py → make_csv` writes CSVs.

## Score corpus layout

```
scores/
  <repo_name>/
    reviewed/
      <piece_name>_reviewed.tsv   ← tab-separated harmonic annotations
```

`infer_composer()` in `import_scores.py` maps repo folder prefixes to canonical composer names. The mapping must stay in sync with `composer_mid_life_dates` in `config.py`.

## Key domain concepts

- **root_prog**: integer line-of-fifths difference between consecutive annotation roots (range roughly −10 to +10)
- **progression categories** (S/A/W/I): strong, artificial, weak, identical — classified by `classify_movement_SAWI()` in `utilities.py`
- **prog_weight**: sum of the durations of the two chords flanking a transition, used to weight rare but long-held progressions appropriately
- **"final" vs "uri" system**: the `uri` system was the original labelling scheme; `final` adds the `I` (identical root) category and is the current default

## Configuration

`config.py` holds:
- `OUTPUT_PATH`, `ROOT_PATH`
- `composer_mid_life_dates` dict (used to sort composers chronologically in plots)
- `UNNECESSARY_COLS` — columns dropped from every TSV on load
- Progression category tuples for each system
