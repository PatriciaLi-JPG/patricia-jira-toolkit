---
name: release story points
description: Use when a Scrum Master / TPM asks for "release story points", Jira release story point sums, release capacity/reporting data, or a small release report by entering only a release such as 26.1.30, 26.2.30, or 26.3.10. Covers team aliases, Story Points, DEV/QA estimates, Jira links, and optional Google Sheet/HTML style report output.
metadata:
  short-description: Jira release SP and effort report
---

# Release Story Points Report

Use this skill when the user asks for a release-level Jira report, Story Points sum, team release summary, or "fancy" mini report and provides only a release value.

Default source context:

- Reference Google Sheet: configure in `config/sources.local.json` if your team uses one.
- Jira base URL: `https://jira.ringcentral.com`
- Jira team field JQL id: `cf[17553]`
- Story Points field: `customfield_10422`
- DEV Estimate field: `customfield_25757`
- QA Estimate field: `customfield_25958`
- Production field: `customfield_10570` (`Exist on Production`)
- Embed Bug default definition: matching release/team issues where `issuetype = Bug` and `Exist on Production = No`

Never hardcode Jira tokens in this skill. Use the active session's Jira access, `$env:JIRA_TOKEN`, or ask the user for a token only if Jira access is unavailable.

## Input Parsing

If the user gives only a release like `26.1.30`, treat it as a Jira sprint name, not a fix version:

- Sprint JQL: `sprint = "26.1.30"`
- Do not use `fixVersion` unless the user explicitly asks for fix-version reporting.

If the user includes a team alias, restrict to that team. Examples:

- `Jupiter Titan 26.1.30` -> `project = FIJI`, `cf[17553] = "Phone-J-Titan-XMN"`, `sprint = "26.1.30"`
- `mThor 26.1.30` or `mThor pingpong 26.1.30` -> `project = MTR`, `cf[17553] in ("Phone-M-Ping-XMN","Phone-M-Pong-XMN")`, `sprint = "26.1.30"`
- `voip 26.2.30` -> legacy sprint scope: `project in (FIJI, MTR)`, `cf[17553] = "XMN-VoIP"`, `sprint = "26.2.30"`
- `voip 26.3.10` and later -> expanded scope: FIJI/MTR VoIP by sprint, plus LI by Log Insight fixVersion, plus RCVR by Rooms fixVersion with `cf[17553] = "XMN-VoIP"`.

Default team aliases:

| Alias | Project | Team JQL |
| --- | --- | --- |
| Jupiter Titan | FIJI | `cf[17553] = "Phone-J-Titan-XMN"` |
| Jupiter IND | FIJI | `cf[17553] = "Phone-Jupiter-IND"` |
| EU Jupiter | FIJI | `cf[17553] = "EU-Jupiter-team"` |
| VoIP | FIJI/MTR + Q3+ extras | Q1/Q2 legacy: `project in (FIJI, MTR) AND cf[17553] = "XMN-VoIP" AND sprint = "<release>"`; Q3+ expanded scope below |
| mThor Ping&Pong | MTR | `cf[17553] in ("Phone-M-Ping-XMN","Phone-M-Pong-XMN")`; this is the only mThor scope for this report |

If the alias is unclear, make a reasonable Jira query and state the assumption briefly.

## VoIP Scope Rule

For VoIP productivity / story point reporting:

- Q1/Q2 2026 historical trend numbers may rely on a manually maintained velocity sheet because several SP entries were manually added from other projects. Do not overwrite those historical numbers unless the user explicitly asks for a current Jira re-run.
- From Q3 2026 onward, use the current Jira expanded VoIP scope by default:

```jql
-- FIJI/MTR VoIP work, sprint-based
project in (FIJI, MTR)
AND cf[17553] = "XMN-VoIP"
AND sprint = "<release>"

-- Log Insight work, fixVersion-based
project = LI
AND fixVersion = "Log Insight <release>"

-- Rooms VoIP work, fixVersion + VoIP team mapping
project = RCVR
AND cf[17553] = "XMN-VoIP"
AND fixVersion = "Rooms <release>"
```

Important: Do not include all RCVR / Rooms tickets. Only include RCVR tickets when `cf[17553] = "XMN-VoIP"`. LI can be included directly by `Log Insight <release>` fixVersion.

If a Q3+ expanded source fixVersion does not exist yet, such as `Log Insight 26.3.10`, skip that source with a short warning instead of failing the whole report.

## Default Metrics

Always report:

- Total issue count.
- Story Points sum across all matching issues.
- Delivery Story Points sum for `User Story`, `Technical task`, and `Improvement`.
- Story Points by issue type.
- Story Points by status.
- Embed Bug count: count only `issuetype = Bug` issues where `Exist on Production = No` in the matching release/team scope.
- Bug Ratio: `Embed Bug count / Total Story Points`; show as both decimal and percent. If Story Points is 0, show `N/A`.
- Active/open issue list when any are not Closed/Done/Resolved/Cancelled.
- Missing Story Points count.
- DEV Estimate and QA Estimate sum when those fields are populated.

## Jira Saved Filter Rules

When creating Jira saved filters for a teammate or shared report:

- Do not leave filters private by default.
- Add a suitable share permission so company Jira users can view the filter. In RingCentral Jira, use global view permission when the user asks for a filter that teammates/company users need to open.
- Do not grant edit permission unless the user explicitly asks.
- After creating or updating a saved filter, read back `sharePermissions` / `/permission` and verify that view sharing is present.
- Include the filter link and the final JQL in the response.

For quarter-level Phone/VoIP output reports, do not count completed Epics by sprint. Count Epics by fixVersion because most Epics do not carry sprint:

- Jupiter Phone / Titan Qx: `issuetype = Epic AND fixVersion in ("Jupiter Web 26.x.10", "Jupiter Web 26.x.20", "Jupiter Web 26.x.30")`
- mThor Ping&Pong Qx: `issuetype = Epic AND fixVersion in ("mThor 26.x.10", "mThor 26.x.20", "mThor 26.x.30")`
- VoIP Qx: include both Jupiter Web and mThor quarter fixVersions under `project in (FIJI, MTR)` with `cf[17553] = "XMN-VoIP"`
- Completed Epic requires `statusCategory = Done AND status != Cancelled`.

For a quick answer, keep it short and include the exact JQL used.

For a report request, create a mini report with:

- KPI block: issue count, total SP, delivery SP, active count, missing SP, DEV/QA sums.
- Bug KPI block: embed bug count and bug ratio.
- Team breakdown table.
- Issue detail table with clickable Jira links.
- Action list: active issues, missing estimates, and any unusual cancelled/open mix.

## Script

For deterministic Jira pulls, use:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\release-story-points-report\scripts\jira_release_report.ps1" -Release "26.1.30"
```

Useful options:

```powershell
# One team only
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\release-story-points-report\scripts\jira_release_report.ps1" -Release "26.1.30" -TeamAlias "Jupiter Titan"

# Save CSV and HTML report
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\release-story-points-report\scripts\jira_release_report.ps1" -Release "26.1.30" -OutDir ".\release-reports" -Html
```

The script reads `JIRA_TOKEN` from the environment unless `-Token` is provided.

## Output Style

Use Scrum Master / TPM style:

- Be concise and executive-readable.
- Preserve Jira IDs, sprint names, team names, and JQL.
- Highlight next actions for missing estimates, open tickets, or stale release ownership.
- When producing a fancy report, prefer a clean operations dashboard style over a marketing page.
