"""Update the existing SVG from a GitHub GraphQL response on standard input."""

import json
from pathlib import Path
import re
import sys


def main():
    response = json.load(sys.stdin)
    if response.get("errors"):
        raise ValueError("GitHub returned GraphQL errors; keeping the existing card")
    user = response["data"]["user"]
    commits = user["contributionsCollection"]["totalCommitContributions"]
    prs = user["pullRequests"]["totalCount"]
    if any(type(value) is not int or value < 0 for value in (commits, prs)):
        raise ValueError("GitHub counts must be non-negative integers")

    card = Path(__file__).resolve().parents[1] / "assets/contribution-stats.svg"
    original = card.read_text(encoding="utf-8")
    updated = original
    replacements = {
        "stats-description": (
            f"Total commits in the last year: {commits}. Total pull requests: {prs}."
        ),
        "commit-count": str(commits),
        "pr-count": str(prs),
    }
    for element_id, value in replacements.items():
        pattern = rf'(<(?:desc|text)\b[^>]*\bid="{element_id}"[^>]*>)[^<]*(</(?:desc|text)>)'
        updated, count = re.subn(pattern, lambda match: match[1] + value + match[2], updated)
        if count != 1:
            raise ValueError(f"Expected exactly one {element_id} element; keeping the existing card")

    if updated != original:
        card.write_text(updated, encoding="utf-8")
    print(f"Contribution statistics: {commits} commits, {prs} pull requests")


if __name__ == "__main__":
    main()
