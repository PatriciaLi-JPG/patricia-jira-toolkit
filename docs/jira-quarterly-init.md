# Jira Quarterly INIT First-Time Use

This skill is intentionally generic. It does not know your team's Jira fields, team names, quarter date windows, or owner fallback rules until you provide them.

## 5-Minute Dry-Run Path

Use this when you only want a safe preview and do not want to edit config yet.

1. Copy the skill folder into Codex.
2. Make sure Jira access is available through your connector or local environment, for example `JIRA_PAT` or `JIRA_USERNAME` / `JIRA_API_TOKEN`.
3. Open a new Codex thread.
4. Paste this prompt and replace the bracketed values:

```text
JIRA Quarter Planning dry-run only.

Jira base URL: [https://jira.example.com]
Target quarter: [2026Q3]
Source template INIT: [INIT-12345]
Target parent INIT, if already created: [INIT-67890 or none]
Editable projects: [PROJ1, PROJ2]
In-scope teams: [Team-A, Team-B]
External projects to ignore: [EXT1, EXT2]
Quarter target dates: [2026-07-01 to 2026-09-30]

Do not create or update Jira. Produce a dry-run operation list with assumptions, ownership conflicts, skipped items, and missing config.
```

This is enough for a first successful preview. The skill should ask only for the smallest missing item if something critical is unclear.

## Install

Copy the skill folder:

```powershell
Copy-Item -Recurse .\skills\jira-quarterly-init $env:USERPROFILE\.codex\skills\
```

Open a new Codex thread after copying.

## Optional Reusable Config

After the first dry-run works, create a reusable local config so you do not need to paste the same team scope every time.

Copy the example config:

```powershell
Copy-Item `
  .\skills\jira-quarterly-init\references\quarterly-init-config.example.json `
  $env:USERPROFILE\.codex\skills\jira-quarterly-init\references\quarterly-init.local.json
```

Edit only these required fields first:

- Jira base URL
- canonical INIT template
- editable projects
- external projects
- in-scope teams
- quarter target start/end dates

For a shorter explanation, see:

```text
skills/jira-quarterly-init/references/quarterly-init-config-guide.md
```

These fields are optional for the first dry-run and mainly matter before live updates:

- out-of-scope teams
- owner fallback rules
- DEV/QA estimate policy

Do not commit `quarterly-init.local.json` if it contains private Jira URLs, names, or team data.

## Reusable Config Prompt

Once config exists, use:

```text
JIRA Quarter Planning for 2026Q3 from INIT-12345, dry-run only. Use my local quarterly-init config.
```

For a hygiene scan:

```text
Scan INIT-67890 for 2026Q3 quarter hygiene, dry-run/read-only only. Use in-scope teams Team-A and Team-B, ignore project EXT.
```

## Live Update Guardrails

- Dry-run first.
- Do not overwrite non-empty Team values.
- Do not change status, Parent Link, or Epic Link unless explicitly requested.
- Re-read issues immediately before every live update.
- For more than five issues, require an operation list before writing.
