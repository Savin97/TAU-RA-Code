---
name: project-tasks-june2026
description: "Weekly meeting tasks assigned by professor, June 2026"
metadata: 
  node_type: memory
  type: project
  originSessionId: ec6565e1-cbe7-4142-94ec-dc19b29f9572
---

Three tasks assigned by Uri (professor), week of 2026-06-09:

1. **Compression analysis**: Explore whether root progressions can compress harmonic annotation Y. For piece X with analysis Y, n-gram representation Z should offer measurable compression. Evaluate effectiveness (discrimination ratio: intra vs inter-composer cosine similarity) and cost (vocabulary explosion, sparsity).

2. **RAM fix for n=4**: Pipeline crashes OOM at n=4. Root cause: `itertools.product(range(rp_min, rp_max+1), repeat=4)` produces ~400K–900K keys used to build dense per-piece CSVs AND a dense piece_matrix of 1284 × vocab × 8 bytes ≈ 4–9 GB.

3. **ZIPs for n=1..4**: Run pipeline for each n and package sparse CSV outputs (per-composer + per-piece n-gram weighted CSVs). Assess how each level adds to analysis.

**Why:** Professor wants to publish / present results showing compression properties and multi-level n-gram analysis.
**How to apply:** Tasks are interdependent — fix RAM first (enables n=4 run), then zip outputs.

## Status as of 2026-06-10: ALL THREE TASKS COMPLETE

**All files changed:**
- `functions/compression_analysis.py` — NEW. `compute_piece_compression_stats()` and `compute_corpus_effectiveness()`.
- `functions/utilities.py` — added `create_output_zip(n, system)`.
- `pipeline/pipeline.py` — full rewrite: sparse CSVs, n in output paths, observed vocab for piece_matrix (float32), compression stats output.
- `main.py` — loops n=1..4, calls `create_output_zip` after each run.
- `tests/test_pipeline_refactor.py` — NEW. 4 tests covering sparse CSV roundtrip, matrix entry correctness, vocab memory savings, compression stats.
- `tests/baseline_results.txt` — saved passing test output.

**Key finding during testing:** old dense CSV had a bug — it could silently miss n-grams whose values fell outside the per-piece rp_min/rp_max range. Sparse approach is more correct.

**On n=3 (5 Bach pieces): cartesian vocab=8,000 → observed=338 (95.8% smaller).**
