import re

from datetime import datetime
from django.utils import timezone


# files matches any of the regex will not be counted
# towards commit stats
IGNORE_PATTERNS = [
    re.compile("^vendor/"),
    re.compile(".*\\.jar$"),
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


def tz_aware_now() -> timezone:
    return timezone.make_aware(datetime.now())
