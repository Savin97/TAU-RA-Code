import requests, configparser
from pathlib import Path

GITHUB_API = "https://api.github.com/repos/DCMLab"
url_for_repo_names = "https://raw.githubusercontent.com/DCMLab/distant_listening_corpus/main/.gitmodules"
fetched_text = requests.get(url_for_repo_names).text

config = configparser.ConfigParser()
config.read_string(fetched_text)   # <-- THIS is the fix

repo_names = open("./data/default_repo_names.txt", 'w')

for section in config.sections():
    name = section.replace('submodule "', '').replace('"', '')
    repo_names.write(f"{name}\n")

def download_reviewed_folder(repo_name, target_root="scores"):
    target_dir = Path(target_root) / repo_name / "reviewed"

    if target_dir.exists():
        print(f"{repo_name}: already present")
        return

    target_dir.mkdir(parents=True, exist_ok=True)

    api_url = f"{GITHUB_API}/{repo_name}/contents/reviewed"

    response = requests.get(api_url)
    response.raise_for_status()

    files = response.json()

    for f in files:
        print(f)
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
    print("DOWNLOADING")
    for repo in repo_names:
        download_reviewed_folder(repo)