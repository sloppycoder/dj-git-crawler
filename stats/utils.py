import json
import re
import os

# files matches any of the regex will not be counted
# towards commit stats
IGNORE_PATTERNS = [
    re.compile(
        "^(vendor|Pods|target|YoutuOCWrapper|vos-app-protection|vos-processor|\\.idea|\\.vscode)/."
    ),
    re.compile("^.*(xcodeproj|xcworkspace)/."),
    re.compile(".*\\.(jar|pbxproj|lock|bk|bak|backup|class|swp|sum)$"),
]

GIT_REPO_PATTERN = re.compile("^(http://|https://|ssh://|git@).*.\\.git$")


def should_ignore_path(path: str) -> bool:
    """
    return true if the path should be ignore
    for calculating commit stats
    """
    for regex in IGNORE_PATTERNS:
        if regex.match(path):
            return True
    return False


def is_remote_git_url(path) -> bool:
    return True if GIT_REPO_PATTERN.match(path) else False


def save_stats(stats, file_name):
    with open(f"{file_name}.json", "w") as f:
        json.dump(stats, f, sort_keys=True, indent=4)

    with open(f"{file_name}.csv", "w") as out_f:
        out_f.write("bucket,repo,key,value\n")
        for k1 in stats.keys():
            for k2 in stats[k1].keys():
                for k3 in stats[k1][k2].keys():
                    for k4 in stats[k1][k2][k3]:
                        path = os.path.basename(k1)
                        line = f"{k2},{path},{k3},{k4},{stats[k1][k2][k3][k4]}"
                        # print(line)
                        out_f.write(line + "\n")
