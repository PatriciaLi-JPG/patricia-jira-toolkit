#!/usr/bin/env python3
"""Clone a Jira INIT issue and its subtasks for a target quarter."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


QUARTER_PATTERNS = [
    (re.compile(r"\b20\d{2}Q[1-4]\b", re.IGNORECASE), "compact"),
    (re.compile(r"\bQ[1-4]\s+20\d{2}\b", re.IGNORECASE), "human"),
    (re.compile(r"\bFY\d{2}\s+Q[1-4]\b", re.IGNORECASE), "human"),
]

SAFE_COPY_FIELDS = {
    "description",
    "labels",
    "components",
    "priority",
    "assignee",
    "reporter",
    "duedate",
    "fixVersions",
    "versions",
}

CUSTOM_FIELD_SKIP_HINTS = (
    "rank",
    "sprint",
    "status",
    "resolution",
    "created",
    "updated",
    "last",
    "closed",
)


def parse_source(value: str) -> tuple[str, str]:
    if re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", value):
        base_url = os.environ.get("JIRA_BASE_URL")
        if not base_url:
            raise ValueError("Set JIRA_BASE_URL when passing only an issue key.")
        return base_url.rstrip("/"), value

    parsed = urllib.parse.urlparse(value)
    match = re.search(r"/browse/([A-Z][A-Z0-9]+-\d+)", parsed.path)
    if not parsed.scheme or not parsed.netloc or not match:
        raise ValueError(f"Unsupported Jira issue URL/key: {value}")
    return f"{parsed.scheme}://{parsed.netloc}", match.group(1)


def parse_quarter(raw: str) -> tuple[str, str, str]:
    value = raw.strip().upper().replace("_", " ").replace("-", " ")
    value = re.sub(r"\s+", " ", value)
    patterns = [
        r"^(20\d{2}) Q([1-4])$",
        r"^(20\d{2})Q([1-4])$",
        r"^Q([1-4]) (20\d{2})$",
        r"^Q([1-4])(20\d{2})$",
    ]
    for pattern in patterns:
        match = re.match(pattern, value)
        if not match:
            continue
        groups = match.groups()
        if groups[0].startswith("20"):
            year, qnum = groups[0], groups[1]
        else:
            year, qnum = groups[1], groups[0]
        return f"{year}Q{qnum}", f"Q{qnum} {year}", f"{year}-q{qnum}"
    raise ValueError(f"Unsupported quarter format: {raw!r}. Use values like 2026Q3 or Q3 2026.")


def auth_headers() -> dict[str, str]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
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


class JiraClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = auth_headers()

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.base_url + path
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, method=method, headers=self.headers)
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 401:
                raise RuntimeError(
                    "Jira returned 401 Unauthorized. Set JIRA_PAT or JIRA_USERNAME/JIRA_API_TOKEN "
                    "with Jira create permissions."
                ) from exc
            raise RuntimeError(f"Jira API error {exc.code} for {method} {path}: {body}") from exc

    def fetch_issue(self, key: str) -> dict[str, Any]:
        path = f"/rest/api/2/issue/{urllib.parse.quote(key)}?expand=names,schema&fields=*all"
        return self.request("GET", path)

    def create_issue(self, fields: dict[str, Any]) -> dict[str, Any]:
        payload = {"fields": fields}
        last_error = ""
        for _ in range(6):
            try:
                return self.request("POST", "/rest/api/2/issue", payload)
            except RuntimeError as exc:
                last_error = str(exc)
                errors = extract_field_errors(last_error)
                removable = [field for field in errors if field in payload["fields"]]
                if not removable:
                    break
                for field in removable:
                    payload["fields"].pop(field, None)
                time.sleep(0.2)
        raise RuntimeError(last_error)


def extract_field_errors(message: str) -> list[str]:
    match = re.search(r"(\{.*\})\s*$", message, re.DOTALL)
    if not match:
        return []
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    errors = payload.get("errors") or {}
    if isinstance(errors, dict):
        return list(errors.keys())
    return []


def transform_text(value: Any, compact: str, human: str) -> Any:
    if isinstance(value, str):
        result = value
        for pattern, style in QUARTER_PATTERNS:
            replacement = compact if style == "compact" else human
            result = pattern.sub(replacement, result)
        return result
    if isinstance(value, list):
        return [transform_text(item, compact, human) for item in value]
    if isinstance(value, dict):
        return {key: transform_text(item, compact, human) for key, item in value.items()}
    return value


def custom_field_allowed(field_id: str, names: dict[str, str]) -> bool:
    name = names.get(field_id, field_id).lower()
    return not any(hint in name for hint in CUSTOM_FIELD_SKIP_HINTS)


def build_create_fields(
    issue: dict[str, Any],
    *,
    compact: str,
    human: str,
    parent_key: str | None = None,
    copy_custom_fields: bool = True,
) -> dict[str, Any]:
    source_fields = issue["fields"]
    names = issue.get("names") or {}
    fields: dict[str, Any] = {
        "project": source_fields["project"],
        "issuetype": source_fields["issuetype"],
        "summary": transform_text(source_fields["summary"], compact, human),
    }

    for field in SAFE_COPY_FIELDS:
        value = source_fields.get(field)
        if value not in (None, "", [], {}):
            fields[field] = transform_text(value, compact, human)

    if parent_key:
        fields["parent"] = {"key": parent_key}

    if copy_custom_fields:
        for field_id, value in source_fields.items():
            if not field_id.startswith("customfield_"):
                continue
            if value in (None, "", [], {}):
                continue
            if not custom_field_allowed(field_id, names):
                continue
            fields[field_id] = transform_text(value, compact, human)

    return scrub_read_only_shapes(fields)


def scrub_read_only_shapes(value: Any) -> Any:
    if isinstance(value, list):
        return [scrub_read_only_shapes(item) for item in value]
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if key in {"self", "avatarUrls", "iconUrl"}:
                continue
            cleaned[key] = scrub_read_only_shapes(item)
        return cleaned
    return value


def child_keys(source: dict[str, Any]) -> list[str]:
    subtasks = source.get("fields", {}).get("subtasks") or []
    keys = []
    for subtask in subtasks:
        key = subtask.get("key")
        if key:
            keys.append(key)
    return keys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Jira source issue URL or key.")
    parser.add_argument("--quarter", required=True, help="Target quarter, for example 2026Q3.")
    parser.add_argument("--create", action="store_true", help="Actually create Jira issues. Omit for dry run.")
    parser.add_argument("--output-dir", default=".", help="Directory for creation report.")
    parser.add_argument("--no-custom-fields", action="store_true", help="Do not copy customfield_* values.")
    args = parser.parse_args()

    compact, human, slug = parse_quarter(args.quarter)
    base_url, source_key = parse_source(args.source)
    client = JiraClient(base_url)

    source_issue = client.fetch_issue(source_key)
    subtask_issues = [client.fetch_issue(key) for key in child_keys(source_issue)]
    parent_fields = build_create_fields(
        source_issue,
        compact=compact,
        human=human,
        copy_custom_fields=not args.no_custom_fields,
    )
    child_fields = [
        build_create_fields(
            issue,
            compact=compact,
            human=human,
            copy_custom_fields=not args.no_custom_fields,
        )
        for issue in subtask_issues
    ]

    report: dict[str, Any] = {
        "source": source_key,
        "quarter": compact,
        "mode": "create" if args.create else "dry-run",
        "generated_on": date.today().isoformat(),
        "parent": {
            "source_key": source_key,
            "summary": parent_fields.get("summary"),
            "created_key": None,
        },
        "children": [
            {
                "source_key": issue["key"],
                "summary": fields.get("summary"),
                "created_key": None,
            }
            for issue, fields in zip(subtask_issues, child_fields)
        ],
    }

    if args.create:
        created_parent = client.create_issue(parent_fields)
        parent_key = created_parent["key"]
        report["parent"]["created_key"] = parent_key
        for index, fields in enumerate(child_fields):
            fields["parent"] = {"key": parent_key}
            created_child = client.create_issue(fields)
            report["children"][index]["created_key"] = created_child["key"]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"jira-clone-{source_key}-{slug}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(report_path)
    if args.create:
        print(f"Created parent: {report['parent']['created_key']}")
        for child in report["children"]:
            print(f"Created child: {child['created_key']} from {child['source_key']}")
    else:
        print("Dry run only. Re-run with --create to create Jira issues.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
