# to use this script to clone all repos to local directory
#
# python3 clone.py | bash
#

import json
import os
import urllib.request

cwd = os.getcwd()
base_dir = os.path.expanduser("~/Projects/ktb/kcorp-dev/gitlab/")

with urllib.request.urlopen("http://10.9.107.120:8000/stats/repo?code=s3cr3t") as f:
    repo_list = json.loads(f.read(100000).decode("utf-8"))
    for repo_url in repo_list:
        repo_url = repo_url.strip()
        parts = repo_url.split("/")
        local_path = base_dir + "/".join(parts[1:-1])
        local_repo = parts[-1].replace(".git", "")
        print(f"### repo {repo_url} in {local_path}/{local_repo} directory")

        if os.path.isdir(f"{local_path}/{local_repo}/.git"):
            print(f"cd {local_path}/{local_repo}")
            print("pwd")
            print("git fetch")
            print("git pull")
            print("")
        else:
            print(f"mkdir -p {local_path}")
            print(f"cd {local_path}")
            print("pwd")
            print(f"git clone {repo_url}")

        print()

print(f"cd {cwd}")
