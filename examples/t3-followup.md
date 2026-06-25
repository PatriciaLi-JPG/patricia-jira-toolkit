# Example: T3 Follow-Up

Prompt:

```text
T3 List followup for FIJI-12345, MTR-67890
```

Expected output shape:

| Ticket | Status | Assignee / @who | Why follow | Suggested ask |
| --- | --- | --- | --- | --- |
| FIJI-12345 | In Progress | @Owner | No meaningful update for 7+ days | Please confirm current blocker and ETA. |

Message draft:

```text
Hi team, could you please help update the following Jira tickets?

Priority items:
- FIJI-12345 @Owner: No meaningful update for 7+ days. Please confirm current blocker and ETA.

Thanks. Please update the Jira comments directly so we can track the latest status.
```

