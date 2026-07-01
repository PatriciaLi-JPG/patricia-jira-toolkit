#!/usr/bin/env python3
"""Convert Jira issue JSON exports into a quarterly template starter."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


QUARTER_PATTERNS = [
    (re.compile(r"\b20\d{2}Q[1-4]\b", re.IGNORECASE), "{{quarter}}"),
    (re.compile(r"\bQ[1-4]\s+20\d{2}\b", re.IGNORECASE), "{{quarter_human}}"),
    (re.compile(r"\bFY\d{2}\s+Q[1-4]\b", re.IGNORECASE), "{{quarter_human}}"),
]


def normalize_text(value: Any) -> Any:
    if isinstance(value, str):
        result = value
        for pattern, replacement in QUARTER_PATTERNS:
            result = pattern.sub(replacement, result)
        return result
    if isinstance(value, list):
        return [normalize_text(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_text(item) for key, item in value.items()}
    return value


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return value[:64] or "issue"


def field_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("value") or "")
    return str(value or "")


def field_names(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [field_name(item) for item in value if field_name(item)]
    name = field_name(value)
    return [name] if name else []


def extract_issue(issue: dict[str, Any], *, as_epic: bool) -> dict[str, Any]:
    fields = issue.get("fields", {})
    summary = normalize_text(fields.get("summary") or issue.get("summary") or issue.get("key") or "")
    item = {
        "id": slugify(str(summary)),
        "summary": summary,
        "description": normalize_text(fields.get("description") or ""),
        "labels": normalize_text(fields.get("labels") or []),
        "components": normalize_text(field_names(fields.get("components"))),
        "priority": field_name(fields.get("priority")),
        "assignee": field_name(fields.get("assignee")),
    }

    story_points = (
        fields.get("customfield_10002")
        or fields.get("customfield_10016")
        or fields.get("story_points")
    )
    if story_points not in (None, ""):
        item["story_points"] = story_points

    due_date = fields.get("duedate")
    if due_date:
        item["due_date"] = normalize_text(due_date)

    if as_epic:
        item["epic_name"] = normalize_text(
            fields.get("customfield_10011")
            or fields.get("epic_name")
            or summary
        )
        item["tasks"] = []
    else:
        issue_type = field_name(fields.get("issuetype"))
        if issue_type:
            item["issue_type"] = issue_type

    return {key: value for key, value in item.items() if value not in ("", [], {}, None)}


def load_issues(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if "issues" in payload and isinstance(payload["issues"], list):
        return payload["issues"]
    return [payload]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Jira issue JSON export or search result JSON.")
    parser.add_argument("--output", required=True, help="Output quarterly-templates.json path.")
    parser.add_argument("--project-key", default="PROJ")
    args = parser.parse_args()

    issues = load_issues(Path(args.input))
    if not issues:
        raise ValueError("No issues found in input JSON.")

    root = issues[0]
    epic = extract_issue(root, as_epic=True)

    children = issues[1:]
    subtasks = root.get("fields", {}).get("subtasks") or []
    for child in children + subtasks:
        epic["tasks"].append(extract_issue(child, as_epic=False))

    template = {
        "defaults": {
            "project_key": args.project_key,
            "issue_type_names": {
                "epic": "Epic",
                "task": "Task",
            },
            "labels": ["quarterly-init"],
            "components": ["Planning"],
            "priority": "Medium",
        },
        "epics": [epic],
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
