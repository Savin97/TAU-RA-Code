import requests
from pathlib import Path

from config import REPOS

GITHUB_API = "https://api.github.com/repos/DCMLab"


def download_reviewed_folder(repo_name, target_root="scores"):
    target_dir = Path(target_root) / repo_name / "reviewed"

    if target_dir.exists():
        #print(f"{repo_name}: already present")
        return

    target_dir.mkdir(parents=True, exist_ok=True)

    api_url = f"{GITHUB_API}/{repo_name}/contents/reviewed"

    response = requests.get(api_url)
    response.raise_for_status()

    files = response.json()

    for f in files:
        if f["type"] != "file":
            continue
        if f["name"].endswith(".tsv"):
            download_url = f["download_url"]
            filename = target_dir / f["name"]

            print(f"Downloading {repo_name}/{f['name']}")

            file_data = requests.get(download_url).content
            filename.write_bytes(file_data)

    print(f"{repo_name}: done")

def download_scores():
    for repo in REPOS:
        download_reviewed_folder(repo)
