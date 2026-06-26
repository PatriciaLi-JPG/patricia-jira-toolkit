# Scrum Master Codex Toolkit

Shared Codex skills, templates, and setup notes for Scrum Master / TPM Jira workflows.

## What's Included

- `skills/release-story-points-report`: release-level Jira SP, effort, bug ratio, active issue, and missing estimate reporting.
- `skills/t3-list-followup`: stale Jira ticket review and send-ready follow-up drafts.
- `config/*.example.json`: sample team, Jira field, and source configuration.
- `templates/`: paste-ready weekly summary, release health, and follow-up message formats.
- `docs/`: setup, Jira auth, and sharing safety notes.
- `mcp/`: MCP setup notes and sample config placeholders.
- `examples/orbit-sudoku`: a small Vite/React game remix that demonstrates a complete Codex coding loop with tests.

## Quick Start

1. Clone this repo.
2. Copy the desired skill folders into your Codex skills directory:

   ```powershell
   Copy-Item -Recurse .\skills\release-story-points-report $env:USERPROFILE\.codex\skills\
   Copy-Item -Recurse .\skills\t3-list-followup $env:USERPROFILE\.codex\skills\
   ```

3. Configure Jira access for your local session:

   ```powershell
   $env:JIRA_TOKEN = "<your-token>"
   ```

4. Open a new Codex thread and try:

   ```text
   release story points 26.3.10
   ```

   ```text
   T3 List followup for FIJI-12345, MTR-67890
   ```

## Sharing Rules

- Do not commit Jira tokens, cookies, personal API keys, or exported customer data.
- Use `config/*.example.json` for team-specific defaults.
- Keep personal saved filters or spreadsheets in local config unless the whole SM team should use them.
- Dry-run before any workflow that writes to Jira, Sheets, or saved filters.

