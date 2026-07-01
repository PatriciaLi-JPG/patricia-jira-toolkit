# Jira Quarterly INIT First-Time Use

This skill is intentionally generic. It does not know your team's Jira fields, team names, quarter date windows, or owner fallback rules until you provide them.

## Install

Copy the skill folder:

```powershell
Copy-Item -Recurse .\skills\jira-quarterly-init $env:USERPROFILE\.codex\skills\
```

Open a new Codex thread after copying.

## Configure

Copy the example config:

```powershell
Copy-Item `
  .\skills\jira-quarterly-init\references\quarterly-init-config.example.json `
  $env:USERPROFILE\.codex\skills\jira-quarterly-init\references\quarterly-init.local.json
```

Edit the local file with your team's values:

- Jira base URL
- canonical INIT template
- editable projects
- external projects
- in-scope teams
- out-of-scope teams
- quarter target start/end dates
- owner fallback rules
- DEV/QA estimate policy

Do not commit `quarterly-init.local.json` if it contains private Jira URLs, names, or team data.

## First Prompt

Start read-only:

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

