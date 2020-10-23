import re

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
