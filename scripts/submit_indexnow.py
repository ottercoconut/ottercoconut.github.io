#!/usr/bin/env python3
"""Submit URL batches to IndexNow."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse


DEFAULT_ENDPOINT = "https://api.indexnow.org/indexnow"
MAX_URLS_PER_REQUEST = 10_000


def chunks(items: list[str], size: int):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def submit(endpoint: str, host: str, key: str, urls: list[str]) -> None:
    payload = json.dumps(
        {
            "host": host,
            "key": key,
            "urlList": urls,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        status = response.getcode()
        if status not in {200, 202}:
            raise RuntimeError(f"IndexNow returned HTTP {status}")
        print(f"Submitted {len(urls)} URL(s) to IndexNow: HTTP {status}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url_file")
    parser.add_argument("--endpoint", default=os.getenv("INDEXNOW_ENDPOINT", DEFAULT_ENDPOINT))
    parser.add_argument("--host", default=os.getenv("INDEXNOW_HOST", ""))
    args = parser.parse_args()

    key = os.getenv("INDEXNOW_KEY", "").strip()
    if not key:
        print("INDEXNOW_KEY is not set; skipping IndexNow submission.")
        return 0

    with open(args.url_file, encoding="utf-8") as file:
        urls = [line.strip() for line in file if line.strip()]

    if not urls:
        print("No changed page URLs to submit to IndexNow.")
        return 0

    host = args.host.strip() or urlparse(urls[0]).netloc
    try:
        for batch in chunks(urls, MAX_URLS_PER_REQUEST):
            submit(args.endpoint, host, key, batch)
    except urllib.error.HTTPError as exc:
        print(f"IndexNow submission failed: HTTP {exc.code}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"IndexNow submission failed: {exc.reason}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
