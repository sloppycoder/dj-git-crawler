import re

# files matches any of the regex will not be counted
# towards commit stats
IGNORE_PATTERNS = [
    re.compile("^vendor/"),
    re.compile(".*\\.jar$"),
]


def should_ignore_path(path: str) -> bool:
    """
    return true if the path should be ignore
    for calculating commit stats
    """
    for regex in IGNORE_PATTERNS:
        if regex.match(path):
            return True
    return False
