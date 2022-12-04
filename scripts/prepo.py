import os
import sys
from configparser import ConfigParser

import django
import requests

requests.packages.urllib3.disable_warnings()
# since this script sits in a subdirectory of the main django project
# add django main project path to sys.path
cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(f"{cwd}/.."))


def print_all_repos(ini_file: str):
    conf = ConfigParser()
    with open(ini_file, "r") as f:
        conf.read_file(f)
        for _, params in enumerate_repositories_by_config(conf):
            print(params["repo_url"])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 prepo.py <ini_file>")
        sys.exit(1)

    ini_file = os.path.abspath(sys.argv[1])

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crawler.settings")
    django.setup()
    from stats.indexer import enumerate_repositories_by_config  # noqa

    print_all_repos(ini_file)
