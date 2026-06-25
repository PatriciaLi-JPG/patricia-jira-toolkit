---
name: t3-list-followup
description: Use when a Scrum Master / TPM asks for "T3 List followup", "t3-list-followup", T3 support ticket follow-up, Jira tickets that need follow-up, stale Jira tickets, tickets with no assignee, tickets missing clear next steps, or asks "哪些 ticket 需要追更新", "帮我整理要追谁", or "追更新草稿". Queries Jira, identifies follow-up candidates, and drafts an at-mentioned message.
---

# T3 List Followup

## Purpose

Identify Jira tickets a Scrum Master / TPM should chase and produce a concise, send-ready follow-up draft.

## Inputs

Accept any of these:
- A list of Jira keys.
- A JQL query.
- A Google Sheet / Jira filter that contains Jira keys.

Default stale threshold: 7 days without meaningful Jira update.

Default T3 source spreadsheet when the user does not provide a link:
configure `t3FollowupSourceSheet` in `config/sources.local.json`, or ask the user for a sheet / Jira filter / Jira key list.

## Source Sheet Rule

When the input is a Google Sheet, or the user says to run T3 List followup without giving explicit Jira keys:

1. Open the source spreadsheet and inspect all tabs/sheets first.
2. Pick the latest weekly source tab, not the previously used tab.
   - Prefer the tab with the latest date in the tab name, such as `06/03`, `2026-06-03`, `Jun 03`, or similar.
   - If multiple tabs have dates, normalize dates to the current year unless the tab includes a year.
   - If the latest tab is empty or clearly not a data source tab, use the latest non-empty data tab and mention the fallback.
   - If no tab name contains a date, use the most recently positioned non-empty source tab and state that the latest tab could not be date-verified.
3. Extract Jira issue keys from that latest tab only.
4. Report which source tab was used before giving the follow-up result.
5. Do not mix older weekly tabs unless the user explicitly asks for comparison.

## Workflow

1. Fetch Jira facts for each issue:
   - key, summary, issue type, status, assignee, team, fix version, updated date, latest comment author/date/body.
   - Use `scripts/jira_followup_tracker.py` when a key list is available.
   - Do not store Jira tokens in the skill. Use the current session credential or pass a token through `JIRA_PAT` / `JIRA_TOKEN`.

2. Classify tickets:
   - **Priority follow-up**: no assignee, no latest comment, stale for 7+ days, unclear owner, unclear next step, "will reassign" without new owner, waiting for external feedback with no ETA, or a decision needed to close / defer.
   - **Clarify next step**: recent activity exists but the next owner or ETA is still ambiguous.
   - **Monitor only**: recent update, clear assignee, clear waiting reason, and no action needed from the Scrum Master yet.

3. Output in Chinese unless the user asks otherwise:
   - First give a short count by category.
   - Then provide a table with `Ticket | Status | Assignee / @who | Why follow | Suggested ask`.
   - Keep issue links clickable: `https://jira.ringcentral.com/browse/KEY`.
   - If the user asks for a message draft, produce a direct Slack/Jira comment draft with @names.

## Follow-up Rules

- Treat `updated` as status/field activity. Treat latest comment as discussion activity.
- A ticket is stale if both the issue update and latest comment are older than the threshold.
- If latest comment is older than threshold but `updated` is recent, still flag it if the update does not explain next action.
- "Waiting for clarification" is not automatically bad; only chase it when the owner, customer ask, ETA, or evidence needed is unclear.
- For closed/resolved tickets, only flag if the user explicitly asks to check FV/cleanup gaps.
- Preserve exact owners, dates, ticket IDs, release/FV, and stated blockers. Do not invent missing ETA or owner.

## Message Style

Use this pattern for send-ready drafts:

```text
Hi team, could you please help update the following Jira tickets?
Some of them are missing a clear owner / next step, or have not had an update for around one week.

Priority items:
- KEY @Name: reason. Please confirm next action / owner / ETA.

Thanks. Please update the Jira comments directly so we can track the latest status.
```

## Script

Run the helper like:

```powershell
$env:JIRA_PAT = '<token for this process only>'
python "$env:USERPROFILE\.codex\skills\t3-list-followup\scripts\jira_followup_tracker.py" --keys "FIJI-1,FIJI-2,MTR-3" --stale-days 7
```
