#!/usr/bin/env python3
"""Clone Epic-level Jira children from one INIT to another for a target quarter."""

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


JIRA_BASE_URL_DEFAULT = "https://jira.example.com"
PARENT_LINK_FIELD = "customfield_15751"
TEAM_FIELD = "customfield_17553"
SPRINT_FIELD = "customfield_10652"
EPIC_NAME_FIELD = "customfield_11451"
EPIC_STATUS_FIELD = "customfield_11452"
ALLOWED_TEAM_HINTS = ("PING", "PONG", "TITAN")
SKIP_STATUSES = {"CANCELLED", "CANCELED"}
SKIP_SUMMARY_PATTERNS = (re.compile(r"\bfull\s*stack\b", re.IGNORECASE),)
SKIP_FIELDS = {
    "attachment",
    "comment",
    "created",
    "creator",
    "customfield_11450",
    "issuelinks",
    "lastViewed",
    "parent",
    "progress",
    "resolution",
    "resolutiondate",
    "status",
    "subtasks",
    "timespent",
    "updated",
    "votes",
    "watches",
    "worklog",
    "workratio",
}


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
                raise RuntimeError("Jira returned 401 Unauthorized. Provide a valid Jira token with create permission.") from exc
            raise RuntimeError(f"Jira API error {exc.code} for {method} {path}: {body}") from exc

    def issue(self, key: str) -> dict[str, Any]:
        return self.request("GET", f"/rest/api/2/issue/{urllib.parse.quote(key)}?expand=names,schema&fields=*all")

    def search(self, jql: str, fields: list[str] | None = None) -> list[dict[str, Any]]:
        start_at = 0
        issues: list[dict[str, Any]] = []
        while True:
            payload: dict[str, Any] = {"jql": jql, "startAt": start_at, "maxResults": 100}
            if fields:
                payload["fields"] = fields
            result = self.request("POST", "/rest/api/2/search", payload)
            issues.extend(result.get("issues", []))
            start_at += result.get("maxResults", 100)
            if start_at >= result.get("total", 0):
                return issues

    def project_versions(self, project_key: str) -> dict[str, dict[str, Any]]:
        result = self.request("GET", f"/rest/api/2/project/{urllib.parse.quote(project_key)}/versions")
        return {item["name"]: item for item in result}

    def board_sprints(self, board_id: int) -> dict[str, dict[str, Any]]:
        sprints: dict[str, dict[str, Any]] = {}
        for state in ("future", "active", "closed"):
            start_at = 0
            while True:
                path = f"/rest/agile/1.0/board/{board_id}/sprint?maxResults=50&startAt={start_at}&state={state}"
                result = self.request("GET", path)
                for sprint in result.get("values", []):
                    sprints[sprint["name"]] = sprint
                start_at += result.get("maxResults", 50)
                if result.get("isLast", True):
                    break
        return sprints

    def create_issue_with_retries(self, fields: dict[str, Any]) -> dict[str, Any]:
        payload = {"fields": fields}
        for _ in range(12):
            try:
                return self.request("POST", "/rest/api/2/issue", payload)
            except RuntimeError as exc:
                removable = removable_fields_from_error(str(exc), payload["fields"])
                if not removable:
                    raise
                for field in removable:
                    payload["fields"].pop(field, None)
                time.sleep(0.2)
        raise RuntimeError("Create failed after removing unsupported fields.")

    def add_issues_to_sprint(self, sprint_id: int, issue_keys: list[str]) -> None:
        self.request("POST", f"/rest/agile/1.0/sprint/{sprint_id}/issue", {"issues": issue_keys})


def removable_fields_from_error(message: str, fields: dict[str, Any]) -> list[str]:
    match = re.search(r"(\{.*\})\s*$", message, re.DOTALL)
    if not match:
        return []
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    errors = payload.get("errors") or {}
    if not isinstance(errors, dict):
        return []
    return [field for field in errors if field in fields and field not in {"project", "issuetype", "summary", PARENT_LINK_FIELD}]


def parse_quarter(value: str) -> tuple[str, str, str, str]:
    raw = value.strip().upper().replace("_", " ").replace("-", " ")
    match = re.match(r"^(?:Q([1-4])\s*(20\d{2})|(20\d{2})\s*Q([1-4])|(20\d{2})Q([1-4]))$", raw)
    if not match:
        raise ValueError(f"Unsupported quarter format: {value}")
    qnum = next(group for group in (match.group(1), match.group(4), match.group(6)) if group)
    year = next(group for group in (match.group(2), match.group(3), match.group(5)) if group)
    yy = year[-2:]
    return f"{year}Q{qnum}", f"Q{qnum} {year}", f"{yy}.{qnum}", f"{yy}Q{qnum}"


def transform_text(value: Any, compact: str, human: str, train: str, short: str) -> Any:
    if isinstance(value, str):
        result = value
        result = re.sub(r"\b20\d{2}Q[1-4]\b", compact, result, flags=re.IGNORECASE)
        result = re.sub(r"\b20\d{2}-Q[1-4]\b", compact.replace("Q", "-Q"), result, flags=re.IGNORECASE)
        result = re.sub(r"\bQ[1-4]\s*20\d{2}\b", human, result, flags=re.IGNORECASE)
        result = re.sub(r"\bQ[1-4]'(\d{2})\b", f"Q{human[1]}'\\1", result, flags=re.IGNORECASE)
        result = re.sub(r"\b\d{2}Q[1-4]\b", short, result, flags=re.IGNORECASE)
        result = re.sub(r"\b\d{2}\.[1-4](?=\.\d{2}\b)", train, result)
        result = re.sub(r"\b\d{2}\.[1-4]\b", train, result)
        return result
    if isinstance(value, list):
        return [transform_text(item, compact, human, train, short) for item in value]
    if isinstance(value, dict):
        return {key: transform_text(item, compact, human, train, short) for key, item in value.items()}
    return value


def team_value(issue: dict[str, Any]) -> str:
    value = issue.get("fields", {}).get(TEAM_FIELD)
    if isinstance(value, dict):
        return str(value.get("value") or value.get("name") or "")
    if isinstance(value, list):
        return ", ".join(str(item.get("value") or item.get("name") or item) for item in value)
    return str(value or "")


def is_allowed_team(team: str) -> bool:
    upper = team.upper()
    return any(hint in upper for hint in ALLOWED_TEAM_HINTS)


def skip_reason(issue: dict[str, Any]) -> str:
    fields = issue.get("fields", {})
    status = str((fields.get("status") or {}).get("name") or "")
    summary = str(fields.get("summary") or "")
    if status.upper() in SKIP_STATUSES:
        return f"status is {status}"
    for pattern in SKIP_SUMMARY_PATTERNS:
        if pattern.search(summary):
            return "full stack Epic excluded"
    team = team_value(issue)
    if not is_allowed_team(team):
        return "team is not Ping/Pong/Titan"
    return ""


def parse_sprint_string(value: Any) -> dict[str, Any] | None:
    if isinstance(value, list):
        for item in value:
            parsed = parse_sprint_string(item)
            if parsed:
                return parsed
        return None
    if not isinstance(value, str) or "name=" not in value:
        return None
    data: dict[str, Any] = {}
    for key in ("id", "name", "rapidViewId"):
        match = re.search(rf"{key}=([^,\]]+)", value)
        if match:
            data[key] = match.group(1)
    if "id" in data:
        data["id"] = int(data["id"])
    if "rapidViewId" in data:
        data["rapidViewId"] = int(data["rapidViewId"])
    return data


def option_ref(value: Any) -> Any:
    if isinstance(value, dict):
        if "id" in value:
            return {"id": str(value["id"])}
        if "value" in value:
            return {"value": value["value"]}
        if "name" in value:
            return {"name": value["name"]}
    if isinstance(value, list):
        return [option_ref(item) for item in value]
    return value


def scrub(value: Any) -> Any:
    if isinstance(value, list):
        return [scrub(item) for item in value]
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if key in {"self", "avatarUrls", "iconUrl"}:
                continue
            cleaned[key] = scrub(item)
        return cleaned
    return value


def map_fix_versions(
    versions: Any,
    project_versions: dict[str, dict[str, Any]],
    compact: str,
    human: str,
    train: str,
    short: str,
) -> tuple[list[dict[str, str]], list[str]]:
    result: list[dict[str, str]] = []
    names: list[str] = []
    for item in versions or []:
        source_name = item.get("name") if isinstance(item, dict) else str(item)
        target_name = transform_text(source_name, compact, human, train, short)
        names.append(str(target_name))
        if target_name in project_versions:
            result.append({"id": str(project_versions[str(target_name)]["id"])})
        else:
            result.append({"name": str(target_name)})
    return result, names


def map_sprint(
    client: JiraClient,
    sprint_value: Any,
    compact: str,
    human: str,
    train: str,
    short: str,
    cache: dict[int, dict[str, dict[str, Any]]],
) -> tuple[Any, str]:
    sprint = parse_sprint_string(sprint_value)
    if not sprint:
        return None, ""
    target_name = str(transform_text(sprint["name"], compact, human, train, short))
    board_id = int(sprint["rapidViewId"])
    if board_id not in cache:
        cache[board_id] = client.board_sprints(board_id)
    target = cache[board_id].get(target_name)
    if target:
        return [int(target["id"])], f"{target_name} ({target['id']})"
    return None, f"{target_name} (not found)"


def build_fields(
    client: JiraClient,
    issue: dict[str, Any],
    target_init: str,
    compact: str,
    human: str,
    train: str,
    short: str,
    version_cache: dict[str, dict[str, dict[str, Any]]],
    sprint_cache: dict[int, dict[str, dict[str, Any]]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source = issue["fields"]
    project_key = source["project"]["key"]
    if project_key not in version_cache:
        version_cache[project_key] = client.project_versions(project_key)

    fields: dict[str, Any] = {
        "project": {"key": project_key},
        "issuetype": {"id": str(source["issuetype"]["id"])},
        "summary": transform_text(source["summary"], compact, human, train, short),
        PARENT_LINK_FIELD: target_init,
    }

    for field_id, value in source.items():
        if field_id in SKIP_FIELDS or value in (None, "", [], {}):
            continue
        if field_id in {"project", "issuetype", "summary", PARENT_LINK_FIELD, "fixVersions", SPRINT_FIELD}:
            continue
        transformed = transform_text(value, compact, human, train, short)
        if field_id in {TEAM_FIELD, "priority", "assignee", "reporter"} or field_id.startswith("customfield_"):
            transformed = option_ref(transformed)
        fields[field_id] = scrub(transformed)

    fields[EPIC_NAME_FIELD] = transform_text(
        source.get(EPIC_NAME_FIELD) or source.get("summary"), compact, human, train, short
    )
    if source.get("fixVersions"):
        mapped_versions, version_names = map_fix_versions(
            source["fixVersions"], version_cache[project_key], compact, human, train, short
        )
        fields["fixVersions"] = mapped_versions
    else:
        version_names = []

    mapped_sprint, sprint_name = map_sprint(client, source.get(SPRINT_FIELD), compact, human, train, short, sprint_cache)
    if mapped_sprint:
        fields[SPRINT_FIELD] = mapped_sprint

    plan = {
        "source_key": issue["key"],
        "project": project_key,
        "source_status": source["status"]["name"],
        "team": team_value(issue),
        "summary": fields["summary"],
        "fix_versions": version_names,
        "sprint": sprint_name,
        "sprint_id": mapped_sprint[0] if mapped_sprint else None,
        "target_parent": target_init,
    }
    return fields, plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-init", required=True)
    parser.add_argument("--target-init", required=True)
    parser.add_argument("--quarter", required=True)
    parser.add_argument("--base-url", default=os.environ.get("JIRA_BASE_URL", JIRA_BASE_URL_DEFAULT))
    parser.add_argument("--output-dir", default=".")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--create", action="store_true")
    args = parser.parse_args()

    compact, human, train, short = parse_quarter(args.quarter)
    client = JiraClient(args.base_url)
    source_init = client.issue(args.source_init)
    target_init = client.issue(args.target_init)

    if source_init["fields"]["issuetype"]["name"].lower() != "initiative":
        raise ValueError(f"{args.source_init} is not an Initiative.")
    if target_init["fields"]["issuetype"]["name"].lower() != "initiative":
        raise ValueError(f"{args.target_init} is not an Initiative.")

    children = client.search(
        f'"Parent Link" = {args.source_init} ORDER BY key',
        ["summary", "issuetype", "status", TEAM_FIELD],
    )
    source_keys: list[str] = []
    skipped: list[dict[str, str]] = []
    for item in children:
        if item["fields"]["issuetype"]["name"] != "Epic":
            continue
        reason = skip_reason(item)
        if reason:
            skipped.append(
                {
                    "key": item["key"],
                    "issue_type": item["fields"]["issuetype"]["name"],
                    "status": item["fields"]["status"]["name"],
                    "team": team_value(item),
                    "summary": item["fields"]["summary"],
                    "reason": reason,
                }
            )
        else:
            source_keys.append(item["key"])

    version_cache: dict[str, dict[str, dict[str, Any]]] = {}
    sprint_cache: dict[int, dict[str, dict[str, Any]]] = {}
    operations: list[dict[str, Any]] = []
    create_fields: list[dict[str, Any]] = []
    for key in source_keys:
        issue = client.issue(key)
        fields, plan = build_fields(
            client, issue, args.target_init, compact, human, train, short, version_cache, sprint_cache
        )
        create_fields.append(fields)
        operations.append(plan)

    created: list[dict[str, str]] = []
    if args.create:
        for fields, plan in zip(create_fields, operations):
            created_issue = client.create_issue_with_retries(fields)
            plan["created_key"] = created_issue["key"]
            created.append({"source_key": plan["source_key"], "created_key": created_issue["key"]})
            if plan.get("sprint_id"):
                client.add_issues_to_sprint(int(plan["sprint_id"]), [created_issue["key"]])
                plan["sprint_added_after_create"] = True

    report = {
        "mode": "create" if args.create else "dry-run",
        "generated_on": date.today().isoformat(),
        "source_init": args.source_init,
        "target_init": args.target_init,
        "target_quarter": compact,
        "source_summary": source_init["fields"]["summary"],
        "target_summary": target_init["fields"]["summary"],
        "operation_count": len(operations),
        "operations": operations,
        "skipped_count": len(skipped),
        "skipped": skipped,
        "created": created,
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"jira-init-epic-clone-{args.source_init}-to-{args.target_init}-{compact.lower()}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"mode={report['mode']}")
    print(f"source={args.source_init} target={args.target_init} quarter={compact}")
    print(f"operations={len(operations)} skipped={len(skipped)}")
    print(path)
    for op in operations:
        print(
            f"{op['source_key']}\t{op['project']}\t{op['team']}\t"
            f"fix={','.join(op['fix_versions'])}\tsprint={op['sprint']}\t{op['summary']}"
        )
    if skipped:
        print("SKIPPED")
        for item in skipped:
            print(f"{item['key']}\t{item['status']}\t{item['team']}\t{item['reason']}\t{item['summary']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
