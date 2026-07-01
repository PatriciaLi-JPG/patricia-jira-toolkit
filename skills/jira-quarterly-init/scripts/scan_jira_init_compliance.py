#!/usr/bin/env python3
"""Read-only compliance scan for a quarterly Jira INIT and its Epic children."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


JIRA_BASE_URL_DEFAULT = "https://jira.example.com"
PARENT_LINK_FIELD = "customfield_15751"
TEAM_FIELD = "customfield_17553"
SPRINT_FIELD = "customfield_10652"
TEAM_KEYS_FIELD = "customfield_28351"
CANCELLED = {"CANCELLED", "CANCELED"}
FINAL_IGNORE_STATUSES = {"CLOSED", "DONE", "RESOLVED"}


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
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(self.base_url + path, data=data, method=method, headers=self.headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 401:
                raise RuntimeError("Jira returned 401 Unauthorized. Set JIRA_PAT or JIRA_USERNAME/JIRA_API_TOKEN.") from exc
            raise RuntimeError(f"Jira API error {exc.code} for {method} {path}: {body}") from exc

    def issue(self, key: str) -> dict[str, Any]:
        fields = [
            "summary",
            "description",
            "issuetype",
            "status",
            "project",
            "labels",
            "components",
            "fixVersions",
            TEAM_FIELD,
            TEAM_KEYS_FIELD,
            SPRINT_FIELD,
            PARENT_LINK_FIELD,
        ]
        query = urllib.parse.urlencode({"fields": ",".join(fields)})
        return self.request("GET", f"/rest/api/2/issue/{urllib.parse.quote(key)}?{query}")

    def child_epics(self, init_key: str) -> list[dict[str, Any]]:
        fields = [
            "summary",
            "description",
            "issuetype",
            "status",
            "project",
            "labels",
            "components",
            "fixVersions",
            TEAM_FIELD,
            TEAM_KEYS_FIELD,
            SPRINT_FIELD,
            PARENT_LINK_FIELD,
        ]
        payload = {
            "jql": f'"Parent Link" = {init_key} AND issuetype = Epic ORDER BY key',
            "startAt": 0,
            "maxResults": 100,
            "fields": fields,
        }
        issues: list[dict[str, Any]] = []
        while True:
            result = self.request("POST", "/rest/api/2/search", payload)
            issues.extend(result.get("issues", []))
            payload["startAt"] += result.get("maxResults", 100)
            if payload["startAt"] >= result.get("total", 0):
                return issues


def parse_quarter(raw: str) -> dict[str, str]:
    value = raw.strip().upper().replace("_", " ").replace("-", " ")
    match = re.match(r"^(?:Q([1-4])\s*(20\d{2})|(20\d{2})\s*Q([1-4])|(20\d{2})Q([1-4]))$", value)
    if not match:
        raise ValueError(f"Unsupported quarter format: {raw}")
    qnum = next(group for group in (match.group(1), match.group(4), match.group(6)) if group)
    year = next(group for group in (match.group(2), match.group(3), match.group(5)) if group)
    yy = year[-2:]
    return {
        "compact": f"{year}Q{qnum}",
        "human": f"Q{qnum} {year}",
        "train": f"{yy}.{qnum}",
        "short": f"{yy}Q{qnum}",
        "qnum": qnum,
        "year": year,
    }


def names(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item.get("name") or item.get("value") or item) for item in value]
    if isinstance(value, dict):
        return [str(value.get("name") or value.get("value") or value)]
    return [str(value)]


def sprint_names(value: Any) -> list[str]:
    output: list[str] = []
    for item in names(value):
        match = re.search(r"name=([^,\]]+)", item)
        output.append(match.group(1) if match else item)
    return [item for item in output if item]


def text_blob(issue: dict[str, Any]) -> str:
    fields = issue.get("fields", {})
    parts: list[str] = [
        str(fields.get("summary") or ""),
        str(fields.get("description") or ""),
        " ".join(str(item) for item in fields.get("labels") or []),
        " ".join(names(fields.get("components"))),
    ]
    return " ".join(parts)


def team_value(issue: dict[str, Any]) -> str:
    fields = issue.get("fields", {})
    return ", ".join(names(fields.get(TEAM_FIELD)))


def project_key(issue: dict[str, Any]) -> str:
    fields = issue.get("fields", {})
    project = fields.get("project") or {}
    return str(project.get("key") or "")


def matches_any(value: str, needles: list[str]) -> bool:
    upper = value.upper()
    return any(needle.upper() in upper for needle in needles if needle)


def has_scope_marker(issue: dict[str, Any], keywords: list[str]) -> bool:
    if not keywords:
        return True
    return matches_any(text_blob(issue), keywords)


def is_quarter_value(value: str, quarter: dict[str, str]) -> bool:
    lower = value.lower()
    patterns = [
        quarter["compact"].lower(),
        quarter["human"].lower(),
        quarter["train"].lower(),
        quarter["short"].lower(),
        f"q{quarter['qnum']}",
    ]
    return any(pattern in lower for pattern in patterns)


def check_issue(
    issue: dict[str, Any],
    quarter: dict[str, str],
    *,
    is_init: bool,
    scope_keywords: list[str],
    in_scope_teams: list[str],
    ignored_projects: set[str],
) -> dict[str, Any]:
    fields = issue["fields"]
    status = fields["status"]["name"]
    summary = fields.get("summary") or ""
    fix_versions = names(fields.get("fixVersions"))
    sprints = sprint_names(fields.get(SPRINT_FIELD))
    team = team_value(issue)
    project = project_key(issue)
    explicit_scope_marker = has_scope_marker(issue, scope_keywords)
    in_scope_team = matches_any(team, in_scope_teams) if in_scope_teams else True

    errors: list[str] = []
    warnings: list[str] = []
    ignored_reason = ""

    if not is_init:
        if project.upper() in ignored_projects:
            ignored_reason = f"Ignored configured external project {project}"
        elif status.upper() in FINAL_IGNORE_STATUSES:
            ignored_reason = f"Ignored final-state Epic ({status})"
        elif in_scope_teams and team and not in_scope_team:
            ignored_reason = "Ignored Epic with populated out-of-scope Team"

    if ignored_reason:
        return {
            "key": issue["key"],
            "issue_type": fields["issuetype"]["name"],
            "status": status,
            "project": project,
            "team": team,
            "summary": summary,
            "fix_versions": fix_versions,
            "sprints": sprints,
            "errors": [],
            "warnings": [],
            "ignored_reason": ignored_reason,
            "ok": True,
        }

    if scope_keywords and not (explicit_scope_marker or in_scope_team):
        errors.append("Missing configured scope marker/team")
    elif scope_keywords and not explicit_scope_marker and in_scope_team:
        warnings.append("No explicit scope marker; Team is in scope")
    if status.upper() in CANCELLED:
        errors.append(f"Status is {status}")
    if re.search(r"\bfull\s*stack\b", summary, re.IGNORECASE):
        errors.append("Summary contains full stack/fullstack")

    if fix_versions:
        bad = [item for item in fix_versions if not is_quarter_value(item, quarter)]
        if bad:
            errors.append("Non-target-quarter Fix Version: " + ", ".join(bad))
    elif not is_init:
        warnings.append("Missing Fix Version")

    if sprints:
        bad = [item for item in sprints if not is_quarter_value(item, quarter)]
        if bad:
            errors.append("Non-target-quarter Sprint: " + ", ".join(bad))
    else:
        warnings.append("Missing Sprint")

    return {
        "key": issue["key"],
        "issue_type": fields["issuetype"]["name"],
        "status": status,
        "project": project,
        "team": team,
        "summary": summary,
        "fix_versions": fix_versions,
        "sprints": sprints,
        "errors": errors,
        "warnings": warnings,
        "ignored_reason": ignored_reason,
        "ok": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init", required=True, help="Target INIT issue key, e.g. INIT-12345.")
    parser.add_argument("--quarter", required=True, help="Target quarter, e.g. 2026Q3.")
    parser.add_argument("--base-url", default=os.environ.get("JIRA_BASE_URL", JIRA_BASE_URL_DEFAULT))
    parser.add_argument("--output-dir", default=".")
    parser.add_argument(
        "--scope-keyword",
        action="append",
        default=[],
        help="Keyword that marks an issue as in scope. Repeat for multiple values.",
    )
    parser.add_argument(
        "--in-scope-team",
        action="append",
        default=[],
        help="Team field value considered in scope. Repeat for multiple values.",
    )
    parser.add_argument(
        "--ignored-project",
        action="append",
        default=[],
        help="Project key to ignore during child Epic scan. Repeat for multiple values.",
    )
    args = parser.parse_args()

    quarter = parse_quarter(args.quarter)
    client = JiraClient(args.base_url)
    init_issue = client.issue(args.init)
    epics = client.child_epics(args.init)
    ignored_projects = {item.upper() for item in args.ignored_project}
    results = [
        check_issue(
            init_issue,
            quarter,
            is_init=True,
            scope_keywords=args.scope_keyword,
            in_scope_teams=args.in_scope_team,
            ignored_projects=ignored_projects,
        )
    ] + [
        check_issue(
            issue,
            quarter,
            is_init=False,
            scope_keywords=args.scope_keyword,
            in_scope_teams=args.in_scope_team,
            ignored_projects=ignored_projects,
        )
        for issue in epics
    ]

    report = {
        "generated_on": date.today().isoformat(),
        "mode": "read-only",
        "init": args.init,
        "quarter": quarter["compact"],
        "issue_count": len(results),
        "epic_count": len(epics),
        "error_count": sum(len(item["errors"]) for item in results),
        "warning_count": sum(len(item["warnings"]) for item in results),
        "results": results,
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"jira-init-compliance-{args.init}-{quarter['compact'].lower()}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"init={args.init} quarter={quarter['compact']} issues={len(results)} epics={len(epics)}")
    print(f"errors={report['error_count']} warnings={report['warning_count']}")
    print(path)
    for item in results:
        if item["errors"] or item["warnings"]:
            print(
                f"{item['key']}\t{item['issue_type']}\t{item['status']}\t"
                f"errors={'; '.join(item['errors']) or '-'}\t"
                f"warnings={'; '.join(item['warnings']) or '-'}\t{item['summary']}"
            )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
