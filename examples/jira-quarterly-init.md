# Example: Jira Quarterly INIT

Prompt:

```text
JIRA Quarter Planning for 2026Q3 from INIT-12345, dry-run only
```

Expected output shape:

- Target quarter:
- Source template:
- Target parent INIT, if any:
- In-scope teams / projects:
- Out-of-scope teams / projects:
- Planned Epics / tasks:
- Missing owner / target date / estimate items:
- Ownership conflicts:
- Blocked Jira fields:
- Dry-run operation list:

Safety expectation:

- Dry-run first.
- Do not overwrite non-empty Team values.
- Do not change status, Parent Link, or Epic Link unless explicitly requested.
- Re-read issues before live updates.
