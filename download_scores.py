import os
import re
import time
from pathlib import Path
from typing import List, Tuple, Optional

import requests

META_REPO = "DCMLab/distant_listening_corpus"
OUT_DIR = Path("dcml_reviewed_tsv")
FILENAME_RE = re.compile(r"_reviewed\.tsv$", re.IGNORECASE)  # change to r"\.tsv$" for all TSVs
SLEEP_SEC = 0.15  # be polite to the API

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # optional but recommended

SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/vnd.github+json"})
if GITHUB_TOKEN:
    SESSION.headers.update({"Authorization": f"Bearer {GITHUB_TOKEN}"})


def http_get(url: str) -> requests.Response:
    r = SESSION.get(url, timeout=60)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise RuntimeError(
            "GitHub rate limit hit. Set environment variable GITHUB_TOKEN to a GitHub PAT."
        )
    r.raise_for_status()
    return r


def fetch_gitmodules_text() -> str:
    url = f"https://raw.githubusercontent.com/{META_REPO}/main/.gitmodules"
    return http_get(url).text


def parse_submodule_paths(gitmodules_text: str) -> List[str]:
    # lines: "path = ABC"
    paths = []
    for line in gitmodules_text.splitlines():
        line = line.strip()
        if line.startswith("path ="):
            paths.append(line.split("=", 1)[1].strip())
    return sorted(set(paths))


def list_reviewed_files(org_repo: str) -> List[Tuple[str, str]]:
    # GitHub Contents API: /contents/reviewed
    url = f"https://api.github.com/repos/{org_repo}/contents/reviewed"
    r = SESSION.get(url, timeout=60)

    if r.status_code == 404:
        return []  # no reviewed folder or repo
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise RuntimeError(
            "GitHub rate limit hit while listing reviewed/. Set GITHUB_TOKEN."
        )
    r.raise_for_status()

    items = r.json()
    out = []
    for it in items:
        if it.get("type") == "file":
            name = it.get("name", "")
            dl = it.get("download_url")
            if dl and FILENAME_RE.search(name):
                out.append((name, dl))
    return out


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = http_get(url)
    dest.write_bytes(r.content)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gm = fetch_gitmodules_text()
    repos = parse_submodule_paths(gm)
    print(f"Found {len(repos)} submodules in {META_REPO}")

    total = 0
    for sub in repos:
        org_repo = f"DCMLab/{sub}"
        files = list_reviewed_files(org_repo)
        if not files:
            continue

        print(f"{sub}: {len(files)} files")
        for name, dl_url in files:
            dest = OUT_DIR / sub / "reviewed" / name
            if dest.exists():
                continue
            download(dl_url, dest)
            total += 1
            time.sleep(SLEEP_SEC)

    print(f"Done. Downloaded {total} TSVs into: {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()