# Scrum Master Codex Toolkit

Shared Codex skills, templates, and setup notes for Scrum Master / TPM Jira workflows.

## What's Included

- `skills/release-story-points-report`: release-level Jira SP, effort, bug ratio, active issue, and missing estimate reporting.
- `skills/t3-list-followup`: stale Jira ticket review and send-ready follow-up drafts.
- `skills/jira-quarterly-init`: generic quarterly INIT/Epic planning, cloning, and hygiene safety rules.
- `config/*.example.json`: sample team, Jira field, and source configuration.
- `templates/`: paste-ready weekly summary, release health, and follow-up message formats.
- `docs/`: setup, Jira auth, and sharing safety notes.
- `mcp/`: MCP setup notes and sample config placeholders.

## Quick Start

1. Clone this repo.
2. Copy the desired skill folders into your Codex skills directory:

   ```powershell
   Copy-Item -Recurse .\skills\release-story-points-report $env:USERPROFILE\.codex\skills\
   Copy-Item -Recurse .\skills\t3-list-followup $env:USERPROFILE\.codex\skills\
   Copy-Item -Recurse .\skills\jira-quarterly-init $env:USERPROFILE\.codex\skills\
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
   T3 List followup for PROJ-12345, PROJ-67890
   ```

   ```text
   JIRA Quarter Planning for 2026Q3, dry-run only
   ```

   For quarterly INIT work, start with [docs/jira-quarterly-init.md](docs/jira-quarterly-init.md). First-time users can run a dry-run by pasting Jira URL, source INIT, quarter, in-scope teams, and editable projects directly into the prompt. A local config is recommended before live Jira updates.

## Sharing Rules

- Do not commit Jira tokens, cookies, personal API keys, or exported customer data.
- Use `config/*.example.json` for team-specific defaults.
- Keep personal saved filters or spreadsheets in local config unless the whole SM team should use them.
- Dry-run before any workflow that writes to Jira, Sheets, or saved filters.
- For quarterly INIT work, configure team scope and owner mapping locally before live Jira updates.
