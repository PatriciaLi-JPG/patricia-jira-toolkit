#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.request


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch Jira issue follow-up facts.")
    parser.add_argument("--keys", help="Comma/space/newline separated Jira issue keys.")
    parser.add_argument("--jql", help="JQL to query. If omitted, --keys is used.")
    parser.add_argument("--jira-base", default="https://jira.ringcentral.com")
    parser.add_argument("--stale-days", type=int, default=7)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def split_keys(raw):
    if not raw:
        return []
    return [k.strip().upper() for k in re.split(r"[\s,;]+", raw) if k.strip()]


def parse_jira_date(value):
    if not value:
        return None
    return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")


def request_json(url, token, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def jira_search(base, token, jql):
    payload = {
        "jql": jql,
        "maxResults": 200,
        "fields": [
            "summary",
            "issuetype",
            "status",
            "assignee",
            "fixVersions",
            "updated",
            "comment",
            "customfield_17553",
        ],
    }
    return request_json(f"{base.rstrip('/')}/rest/api/2/search", token, payload)


def field_values(values):
    if not values:
        return ""
    output = []
    for item in values:
        if isinstance(item, dict):
            output.append(item.get("value") or item.get("name") or str(item))
        else:
            output.append(str(item))
    return ", ".join(output)


def summarize_issue(issue, stale_days):
    fields = issue["fields"]
    comments = fields.get("comment", {}).get("comments", [])
    latest = comments[-1] if comments else None
    updated = parse_jira_date(fields.get("updated"))
    latest_comment_date = parse_jira_date(latest.get("created")) if latest else None
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=stale_days)
    assignee = fields.get("assignee") or {}
    fix_versions = fields.get("fixVersions") or []
    reasons = []
    if not assignee:
        reasons.append("no assignee")
    if not latest:
        reasons.append("no comment")
    if updated and updated < cutoff and (not latest_comment_date or latest_comment_date < cutoff):
        reasons.append(f"stale {stale_days}+ days")
    if fields.get("status", {}).get("name") in {"Open", "In Progress", "Waiting for clarification"}:
        if latest:
            text = latest.get("body", "").lower()
            action_terms = [
                "will re-assign",
                "will reassign",
                "waiting",
                "ask customer",
                "eta",
                "test build",
                "logs",
                "har file",
                "failed case",
                "failed cases",
                "feedback",
                "will update",
                "can't reproduce",
                "cannot reproduce",
                "not much we can do",
                "workaround",
                "permanent fix",
            ]
            if any(term in text for term in action_terms):
                reasons.append("next step/ETA may need confirmation")
    return {
        "key": issue["key"],
        "url": f"https://jira.ringcentral.com/browse/{issue['key']}",
        "type": fields.get("issuetype", {}).get("name", ""),
        "summary": fields.get("summary", ""),
        "status": fields.get("status", {}).get("name", ""),
        "assignee": assignee.get("displayName", "") if assignee else "",
        "team": field_values(fields.get("customfield_17553")),
        "fixVersions": ", ".join(v.get("name", "") for v in fix_versions),
        "updated": fields.get("updated", ""),
        "latestCommentAuthor": latest.get("author", {}).get("displayName", "") if latest else "",
        "latestCommentDate": latest.get("created", "") if latest else "",
        "latestComment": re.sub(r"\s+", " ", latest.get("body", "")).strip() if latest else "",
        "followReasons": reasons,
    }


def print_markdown(rows):
    print("| Ticket | Status | Assignee | FV | Follow reason | Latest progress |")
    print("|---|---|---|---|---|---|")
    for row in rows:
        reason = "; ".join(row["followReasons"]) if row["followReasons"] else "monitor only"
        latest = row["latestComment"]
        if len(latest) > 220:
            latest = latest[:217] + "..."
        print(
            f"| [{row['key']}]({row['url']}) | {row['status']} | {row['assignee'] or 'Unassigned'} | "
            f"{row['fixVersions'] or 'EMPTY'} | {reason} | {latest or 'No comment'} |"
        )


def main():
    args = parse_args()
    token = os.environ.get("JIRA_PAT") or os.environ.get("JIRA_TOKEN")
    if not token:
        print("Set JIRA_PAT or JIRA_TOKEN for this process.", file=sys.stderr)
        return 2
    keys = split_keys(args.keys)
    jql = args.jql or f"key in ({','.join(keys)})"
    data = jira_search(args.jira_base, token, jql)
    rows = [summarize_issue(issue, args.stale_days) for issue in data.get("issues", [])]
    key_order = {key: idx for idx, key in enumerate(keys)}
    rows.sort(key=lambda row: key_order.get(row["key"], len(key_order)))
    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_markdown(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
