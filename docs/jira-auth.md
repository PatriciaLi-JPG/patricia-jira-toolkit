# Jira Authentication

The skills expect Jira credentials from the local environment or an authenticated connector.

## Environment Variables

Preferred:

```powershell
$env:JIRA_TOKEN = "<your-token>"
```

Some scripts also accept:

```powershell
$env:JIRA_PAT = "<your-pat>"
```

For username + token flows:

```powershell
$env:JIRA_USERNAME = "<your-email-or-username>"
$env:JIRA_API_TOKEN = "<your-api-token>"
```

## Safety

- Never commit real tokens.
- Never paste tokens into `SKILL.md`.
- Prefer session-only environment variables.
- If a command fails with `401 Unauthorized`, refresh your local token instead of changing shared skill files.

