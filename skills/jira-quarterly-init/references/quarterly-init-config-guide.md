# Quarterly INIT Config Guide

Use `quarterly-init-config.example.json` as a copy/paste starter.

## Required For First Reusable Dry-Run

- `jiraBaseUrl`
- `canonicalInitTemplate.issueKey` or `canonicalInitTemplate.url`
- `editableProjects`
- `externalProjects`
- `inScopeTeams`
- `quarterDateWindows`

## Optional Until Live Updates

- `outOfScopeTeams`
- `teamFieldJql`
- `fixVersionPatterns`
- `ownerFallbacks`
- `estimatePolicy`

## What To Do When Unsure

- Leave optional values as examples.
- Ask for dry-run only.
- Let Codex list missing config and assumptions.
- Add live-update details only after the dry-run operation list looks right.

## Minimum Config Example

```json
{
  "jiraBaseUrl": "https://jira.example.com",
  "canonicalInitTemplate": {
    "issueKey": "INIT-12345",
    "url": "https://jira.example.com/browse/INIT-12345"
  },
  "editableProjects": ["PROJ"],
  "externalProjects": ["EXT"],
  "inScopeTeams": ["Team-A"],
  "quarterDateWindows": {
    "2026Q3": {
      "targetStart": "2026-07-01",
      "targetEnd": "2026-09-30"
    }
  }
}
```

