# functions/import_scores.py
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
import re

@dataclass(frozen=True)
class PieceRecord:
    composer: str
    repo: str
    score: str
    path: Path

REVIEWED_SUFFIX_RE = re.compile(r"_reviewed$", re.IGNORECASE)

def score_name_from_path(tsv_path: Path) -> str:
    # n01op18-1_01_reviewed.tsv -> n01op18-1_01
    stem = tsv_path.stem
    stem = REVIEWED_SUFFIX_RE.sub("", stem)
    return stem

def infer_composer(repo_name: str) -> str:
    """
        Convert repo folder name -> composer display name.
        Extend rules as needed, but this already covers your repo list well.
    """
    r = repo_name.lower().strip()

    # Special-cases first (because "bach" appears in many)
    if r.startswith("cpe_bach"):
        return "CPE_Bach"
    if r.startswith("wf_bach"):
        return "WF_Bach"
    if r.startswith("jc_bach"):
        return "JC_Bach"
    if r.startswith("c_schumann"):
        return "Clara_Schumann"
    if r.startswith == "abc":
        return "Beethoven"

    # Straight composer prefixes
    prefix_map = {
        "bach": "Bach",
        "beethoven": "Beethoven",
        "chopin": "Chopin",
        "liszt": "Liszt",
        "mozart": "Mozart",
        "bartok": "Bartok",
        "debussy": "Debussy",
        "dvorak": "Dvorak",
        "frescobaldi": "Frescobaldi",
        "grieg": "Grieg",
        "handel": "Handel",
        "kleine": "Schuetz",  # adjust if you want a better label
        "kozeluh": "Kozeluh",
        "mahler": "Mahler",
        "medtner": "Medtner",
        "mendelssohn": "Mendelssohn",
        "monteverdi": "Monteverdi",
        "pergolesi": "Pergolesi",
        "peri": "Peri",
        "pleyel": "Pleyel",
        "poulenc": "Poulenc",
        "rachmaninoff": "Rachmaninoff",
        "ravel": "Ravel",
        "scarlatti": "Scarlatti",
        "schubert": "Schubert",
        "schulhoff": "Schulhoff",
        "schumann": "Schumann",
        "sweelinck": "Sweelinck",
        "tchaikovsky": "Tchaikovsky",
        "wagner": "Wagner",
        "corelli": "Corelli",
        "couperin": "Couperin"
    }

    first_token = r.split("_", 1)[0]
    return prefix_map.get(first_token, repo_name)  # fallback: repo name

def build_piece_paths_list(scores_root: Path) -> list[PieceRecord]:
    """
        Expected layout: scores_root/reviewed/*.tsv
    """
    records = []
    for repo_dir in sorted(p for p in scores_root.iterdir() if p.is_dir()):
        reviewed_dir = repo_dir / "reviewed"
        repo = repo_dir.name
        composer = infer_composer(repo)
        allowed_composers = ["Bach", "Beethoven", "Mozart"]
        if composer in allowed_composers:
            for tsv_path in sorted(reviewed_dir.glob("*.tsv")):
                score = score_name_from_path(tsv_path)
                records.append(PieceRecord(composer=composer, repo=repo, score=score, path=tsv_path))
    return records

def group_by_composer(records: list) -> dict[str, list[PieceRecord]]:
    groups = defaultdict(list)
    for rec in records:
        groups[rec.composer].append(rec)
    return dict(groups)