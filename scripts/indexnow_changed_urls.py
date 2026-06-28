#!/usr/bin/env python3
"""Print IndexNow candidate URLs for changed Hugo content files."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


GLOBAL_SITE_FILES = {
    "config",
    "layouts",
    "assets",
    "static",
    "go.mod",
    "go.sum",
}


def run(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def changed_files(base: str, head: str) -> list[str]:
    output = run(["git", "diff", "--name-only", "--diff-filter=ACMRT", base, head])
    return [line.strip() for line in output.splitlines() if line.strip()]


def hugo_pages() -> list[dict[str, str]]:
    output = run(["hugo", "list", "all"])
    return list(csv.DictReader(output.splitlines()))


def is_global_site_change(path: str) -> bool:
    first = path.split("/", 1)[0]
    return first in GLOBAL_SITE_FILES


def is_indexable_page(row: dict[str, str]) -> bool:
    if row.get("draft", "").lower() == "true":
        return False
    return row.get("kind") in {"home", "page"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()

    files = changed_files(args.base, args.head)
    if not files:
        return 0

    pages = [row for row in hugo_pages() if is_indexable_page(row)]

    if any(is_global_site_change(path) for path in files):
        urls = [row["permalink"] for row in pages if row.get("permalink")]
    else:
        changed_content = {
            str(Path(path))
            for path in files
            if path.startswith("content/") and Path(path).suffix in {".md", ".html"}
        }
        urls = [
            row["permalink"]
            for row in pages
            if row.get("path") in changed_content and row.get("permalink")
        ]

    for url in sorted(set(urls)):
        print(url)

    return 0


if __name__ == "__main__":
    sys.exit(main())
