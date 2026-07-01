#!/usr/bin/env python3
"""Generate quarterly Jira init epics and tasks from a reusable JSON template."""

from __future__ import annotations

import argparse
import calendar
import csv
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


CSV_COLUMNS = [
    "External ID",
    "Parent External ID",
    "Project Key",
    "Issue Type",
    "Summary",
    "Description",
    "Epic Name",
    "Labels",
    "Components",
    "Priority",
    "Assignee",
    "Story Points",
    "Due Date",
    "Quarter",
    "Template ID",
    "Fields JSON",
]


def parse_quarter(raw: str) -> tuple[int, int]:
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
            return int(groups[0]), int(groups[1])
        return int(groups[1]), int(groups[0])
    raise ValueError(f"Unsupported quarter format: {raw!r}. Use values like 2026Q3 or Q3 2026.")


def quarter_context(raw: str, project_key: str | None, extra_vars: dict[str, str]) -> dict[str, str]:
    year, quarter_number = parse_quarter(raw)
    start_month = (quarter_number - 1) * 3 + 1
    end_month = start_month + 2
    end_day = calendar.monthrange(year, end_month)[1]
    context = {
        "quarter": f"{year}Q{quarter_number}",
        "quarter_human": f"Q{quarter_number} {year}",
        "quarter_slug": f"{year}-q{quarter_number}",
        "year": str(year),
        "quarter_number": str(quarter_number),
        "quarter_start": date(year, start_month, 1).isoformat(),
        "quarter_end": date(year, end_month, end_day).isoformat(),
        "generated_on": date.today().isoformat(),
    }
    if project_key:
        context["project_key"] = project_key
    context.update(extra_vars)
    return context


def render(value: Any, context: dict[str, str]) -> Any:
    if isinstance(value, str):
        def replace(match: re.Match[str]) -> str:
            key = match.group(1).strip()
            return str(context.get(key, match.group(0)))

        return re.sub(r"\{\{\s*([a-zA-Z0-9_\-]+)\s*\}\}", replace, value)
    if isinstance(value, list):
        return [render(item, context) for item in value]
    if isinstance(value, dict):
        return {key: render(item, context) for key, item in value.items()}
    return value


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    if value == "":
        return []
    return [str(value)]


def merge_lists(defaults: dict[str, Any], item: dict[str, Any], key: str) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for value in as_list(defaults.get(key)) + as_list(item.get(key)):
        if value not in seen:
            seen.add(value)
            merged.append(value)
    return merged


def build_issue(
    *,
    template_id: str,
    external_id: str,
    parent_external_id: str,
    project_key: str,
    issue_type: str,
    item: dict[str, Any],
    defaults: dict[str, Any],
    quarter: str,
    epic_name: str = "",
) -> dict[str, Any]:
    return {
        "external_id": external_id,
        "parent_external_id": parent_external_id,
        "project_key": item.get("project_key") or project_key,
        "issue_type": item.get("issue_type") or issue_type,
        "summary": item.get("summary", ""),
        "description": item.get("description", ""),
        "epic_name": epic_name,
        "labels": merge_lists(defaults, item, "labels"),
        "components": merge_lists(defaults, item, "components"),
        "priority": item.get("priority") or defaults.get("priority", ""),
        "assignee": item.get("assignee") or defaults.get("assignee", ""),
        "story_points": item.get("story_points", ""),
        "due_date": item.get("due_date", ""),
        "quarter": quarter,
        "template_id": template_id,
        "fields": item.get("fields", {}),
    }


def generate_issues(template: dict[str, Any], context: dict[str, str]) -> list[dict[str, Any]]:
    rendered = render(template, context)
    defaults = rendered.get("defaults", {})
    issue_type_names = defaults.get("issue_type_names", {})
    project_key = context.get("project_key") or defaults.get("project_key")
    if not project_key:
        raise ValueError("Missing project key. Provide defaults.project_key or --project-key.")

    issues: list[dict[str, Any]] = []
    for epic in rendered.get("epics", []):
        epic_id = epic["id"]
        epic_external_id = f"{context['quarter_slug']}-{epic_id}"
        epic_issue = build_issue(
            template_id=epic_id,
            external_id=epic_external_id,
            parent_external_id="",
            project_key=project_key,
            issue_type=issue_type_names.get("epic", "Epic"),
            item=epic,
            defaults=defaults,
            quarter=context["quarter"],
            epic_name=epic.get("epic_name") or epic.get("summary", ""),
        )
        issues.append(epic_issue)

        for task in epic.get("tasks", []):
            task_id = task["id"]
            task_external_id = f"{epic_external_id}-{task_id}"
            issues.append(
                build_issue(
                    template_id=f"{epic_id}/{task_id}",
                    external_id=task_external_id,
                    parent_external_id=epic_external_id,
                    project_key=project_key,
                    issue_type=task.get("issue_type") or issue_type_names.get("task", "Task"),
                    item=task,
                    defaults=defaults,
                    quarter=context["quarter"],
                )
            )
    return issues


def write_json(path: Path, issues: list[dict[str, Any]], context: dict[str, str]) -> None:
    payload = {
        "generated_on": context["generated_on"],
        "quarter": context["quarter"],
        "quarter_start": context["quarter_start"],
        "quarter_end": context["quarter_end"],
        "issue_count": len(issues),
        "issues": issues,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, issues: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for issue in issues:
            writer.writerow(
                {
                    "External ID": issue["external_id"],
                    "Parent External ID": issue["parent_external_id"],
                    "Project Key": issue["project_key"],
                    "Issue Type": issue["issue_type"],
                    "Summary": issue["summary"],
                    "Description": issue["description"],
                    "Epic Name": issue["epic_name"],
                    "Labels": ",".join(issue["labels"]),
                    "Components": ",".join(issue["components"]),
                    "Priority": issue["priority"],
                    "Assignee": issue["assignee"],
                    "Story Points": issue["story_points"],
                    "Due Date": issue["due_date"],
                    "Quarter": issue["quarter"],
                    "Template ID": issue["template_id"],
                    "Fields JSON": json.dumps(issue["fields"], ensure_ascii=False, sort_keys=True),
                }
            )


def write_markdown(path: Path, issues: list[dict[str, Any]], context: dict[str, str]) -> None:
    epic_count = sum(1 for issue in issues if not issue["parent_external_id"])
    task_count = len(issues) - epic_count
    lines = [
        f"# Jira Quarterly Init Preview: {context['quarter_human']}",
        "",
        f"- Project key: {context.get('project_key', '')}",
        f"- Quarter dates: {context['quarter_start']} to {context['quarter_end']}",
        f"- Epics: {epic_count}",
        f"- Tasks: {task_count}",
        "",
        "## Review Checklist",
        "",
        "- [ ] Quarter text and dates are correct",
        "- [ ] Project key, issue types, labels, and components are correct",
        "- [ ] Parent-child links are correct",
        "- [ ] Owners, story points, priorities, and due dates are still current",
        "- [ ] One-off historical details have been removed",
        "",
        "## Issues",
        "",
    ]
    for issue in issues:
        indent = "  - " if issue["parent_external_id"] else "- "
        parent = f" parent={issue['parent_external_id']}" if issue["parent_external_id"] else ""
        lines.append(f"{indent}`{issue['external_id']}` [{issue['issue_type']}] {issue['summary']}{parent}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_vars(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid --var {value!r}. Use KEY=VALUE.")
        key, item = value.split("=", 1)
        result[key.strip()] = item.strip()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, help="Path to quarterly template JSON.")
    parser.add_argument("--quarter", required=True, help="Target quarter, for example 2026Q3 or Q3 2026.")
    parser.add_argument("--project-key", help="Jira project key override.")
    parser.add_argument("--output-dir", default=".", help="Directory for generated artifacts.")
    parser.add_argument("--format", choices=["json", "csv", "md", "all"], default="all")
    parser.add_argument("--var", action="append", default=[], help="Extra template variable as KEY=VALUE.")
    args = parser.parse_args()

    template_path = Path(args.template)
    template = json.loads(template_path.read_text(encoding="utf-8"))
    extra_vars = parse_vars(args.var)
    context = quarter_context(args.quarter, args.project_key, extra_vars)
    if "project_key" not in context:
        default_project_key = template.get("defaults", {}).get("project_key")
        if default_project_key:
            context["project_key"] = str(default_project_key)

    issues = generate_issues(template, context)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base = output_dir / f"jira-quarterly-init-{context['quarter_slug']}"

    written: list[Path] = []
    if args.format in ("json", "all"):
        path = base.with_suffix(".json")
        write_json(path, issues, context)
        written.append(path)
    if args.format in ("csv", "all"):
        path = base.with_suffix(".csv")
        write_csv(path, issues)
        written.append(path)
    if args.format in ("md", "all"):
        path = base.with_suffix(".md")
        write_markdown(path, issues, context)
        written.append(path)

    epic_count = sum(1 for issue in issues if not issue["parent_external_id"])
    task_count = len(issues) - epic_count
    print(f"Generated {epic_count} epics and {task_count} tasks for {context['quarter']}.")
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

