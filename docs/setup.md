# Setup

## Install Skills

Copy any skill folder under `skills/` into your local Codex skills directory.

Windows PowerShell:

```powershell
Copy-Item -Recurse .\skills\release-story-points-report $env:USERPROFILE\.codex\skills\
Copy-Item -Recurse .\skills\t3-list-followup $env:USERPROFILE\.codex\skills\
Copy-Item -Recurse .\skills\jira-quarterly-init $env:USERPROFILE\.codex\skills\
```

macOS / Linux:

```bash
cp -R skills/release-story-points-report ~/.codex/skills/
cp -R skills/t3-list-followup ~/.codex/skills/
cp -R skills/jira-quarterly-init ~/.codex/skills/
```

Start a new Codex thread after copying so the skill list refreshes.

## Configure Local Defaults

Use the files in `config/` as examples. Keep your real config local unless it is approved for team sharing.

Suggested local-only files:

- `config/team-mapping.local.json`
- `config/jira-fields.local.json`
- `config/sources.local.json`
- `config/quarterly-init.local.json`

## Verify

Ask Codex:

```text
release story points 26.3.10
```

or:

```text
T3 List followup for FIJI-12345
```

or:

```text
JIRA Quarter Planning for 2026Q3, dry-run only
```
