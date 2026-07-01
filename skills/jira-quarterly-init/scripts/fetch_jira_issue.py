#!/usr/bin/env python3
"""Fetch a Jira issue JSON using URL/key plus env-based credentials."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


def parse_issue_url(value: str) -> tuple[str, str]:
    if re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", value):
        base_url = os.environ.get("JIRA_BASE_URL")
        if not base_url:
            raise ValueError("Set JIRA_BASE_URL when passing only an issue key.")
        return base_url.rstrip("/"), value

    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Unsupported Jira issue URL/key: {value}")

    match = re.search(r"/browse/([A-Z][A-Z0-9]+-\d+)", parsed.path)
    if not match:
        match = re.search(r"/issue/([A-Z][A-Z0-9]+-\d+)", parsed.path)
    if not match:
        raise ValueError(f"Could not extract Jira issue key from: {value}")

    return f"{parsed.scheme}://{parsed.netloc}", match.group(1)


def auth_headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    pat = os.environ.get("JIRA_PAT")
    if pat:
        headers["Authorization"] = f"Bearer {pat}"
        return headers

    username = os.environ.get("JIRA_USERNAME")
    token = os.environ.get("JIRA_API_TOKEN")
    if username and token:
        raw = f"{username}:{token}".encode("utf-8")
        headers["Authorization"] = "Basic " + base64.b64encode(raw).decode("ascii")
    return headers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Jira browse URL or issue key.")
    parser.add_argument("--output", required=True, help="Output JSON path.")
    parser.add_argument("--fields", default="*all", help="Jira fields parameter.")
    args = parser.parse_args()

    base_url, issue_key = parse_issue_url(args.url)
    api_url = f"{base_url}/rest/api/2/issue/{issue_key}?fields={args.fields}"
    request = urllib.request.Request(api_url, headers=auth_headers())

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            print(
                "Jira returned 401 Unauthorized. Provide JIRA_PAT or JIRA_USERNAME/JIRA_API_TOKEN, "
                "or export/paste the issue JSON manually.",
                file=sys.stderr,
            )
        raise

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

