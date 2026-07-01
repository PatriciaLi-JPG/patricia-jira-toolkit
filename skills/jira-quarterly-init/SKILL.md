---
name: jira-quarterly-init
description: Use when a Scrum Master / TPM asks for Jira quarter planning, quarterly INIT/Epic/Task creation, INIT hygiene checks, target start/end validation, committed default checks, missing DEV/QA estimate lists, cloning or retitling a quarterly INIT template, or preparing a dry-run preview before live Jira API creation.
---

# Jira Quarterly INIT

## Overview

Use this skill to turn a reusable quarterly Jira template or canonical INIT issue into a reviewed set of quarterly INITs, Epics, and child tasks. It also supports read-only hygiene scans for existing quarter planning structures.

Create or update live Jira issues only when the user explicitly asks and authenticated Jira access is available. Prefer dry-run previews for all bulk or ownership-sensitive work.

## Required Local Configuration

This public skill is intentionally team-neutral. Before using it for live Jira writes, the user or team should provide the local planning rules for their org:

- Jira base URL, for example through `JIRA_BASE_URL`.
- Canonical source INIT or template issue.
- Target quarter and target quarter date window.
- In-scope project keys.
- In-scope team field values.
- Out-of-scope project keys or teams.
- Team/owner mapping for blank ownership cases.
- Fix Version and Sprint naming conventions.
- DEV/QA estimate policy.

If any of these are missing, do not guess. Produce a dry-run with assumptions or ask for the smallest missing input.

## Workflow

1. Confirm or infer the target quarter, project key, and output mode.
   - Accept quarters such as `2026Q3`, `Q3 2026`, or `2026-Q3`.
   - If project key, source template, or target parent is missing, infer from team config only when it is explicit; otherwise ask.
2. Locate the reusable template.
   - Prefer `references/quarterly-templates.json` if the team has created one locally.
   - If `references/template-sources.json` exists, use it only as local/team configuration, not as universal truth.
   - If only historical Jira exports are provided, convert them into the template shape described in `references/template-schema.md`.
   - Use `references/quarterly-templates.example.json` only as a starter.
3. Generate a dry-run preview.
   - For template-based creation, use `scripts/generate_quarterly_jira.py`.
   - For direct cloning from Jira, use a clone script in dry-run mode first.
4. Review before live changes.
   - Check quarter tokens, project key, issue types, parent-child links, labels/components, assignees, due dates, story points, DEV/QA estimates, fix versions, sprint values, and team ownership.
   - Flag missing owners, ambiguous components, stale historical wording, and tasks that should no longer repeat.
5. Create or update Jira issues only after explicit approval.
   - Create or clone the parent issue first, capture the created key, then create child items with the correct parent or epic relation.
   - Do not generate CSV unless the user asks for Jira bulk import.

## Historical Data Conversion

When the user provides historical Jira tickets:

- Group issues by Epic / Parent / Initiative where possible.
- Preserve stable fields: summary, description, issue type, labels, components, priority, assignee role, story points, due date pattern, DEV estimate, QA estimate, and acceptance criteria.
- Replace quarter-specific text with template tokens:
  - `2026Q2`, `Q2 2026`, `FY26 Q2` -> `{{quarter}}` or `{{quarter_human}}`
  - quarter start date -> `{{quarter_start}}`
  - quarter end date -> `{{quarter_end}}`
  - project key -> `{{project_key}}` when it should remain configurable
- Keep real team-specific names only when they are intentionally permanent owners or components.
- Remove one-off incident details unless they represent a recurring checklist item.
- If historical examples disagree, prefer the most recent successful quarter and mention the conflict.

Store the cleaned reusable template as `references/quarterly-templates.json` only when the user wants the skill to remember it for future quarters.

## Jira Template Source

When the user gives a Jira URL:

1. Extract the issue key from URLs like `https://jira.example.com/browse/INIT-12345`.
2. Try Jira REST fetch if credentials or an authenticated Jira tool are available.
3. If fetch returns `401` or a login page, ask the user to export or paste the issue fields and any child task list.
4. Convert the fetched/exported issue data into `references/quarterly-templates.json`.

To fetch with environment credentials:

```bash
python scripts/fetch_jira_issue.py --url https://jira.example.com/browse/INIT-12345 --output ./out/INIT-12345.json
```

Supported auth environment variables:

- `JIRA_BASE_URL`: Jira base URL when a script accepts it.
- `JIRA_PAT`: sent as `Authorization: Bearer <token>`.
- `JIRA_USERNAME` and `JIRA_API_TOKEN`: sent as HTTP Basic auth.

Never store Jira tokens or credentials in this skill.

## Direct Jira Creation

Use the clone script when the user asks to create the quarter's Jira tasks directly from a canonical template issue:

```bash
python scripts/clone_jira_issue_tree.py --source https://jira.example.com/browse/INIT-12345 --quarter 2026Q3 --output-dir ./out
```

Add `--create` only after the user has approved the dry-run operation list.

Behavior:

- Fetch the source issue and subtasks with Jira REST.
- Replace quarter text in summaries/descriptions/labels with the requested quarter.
- Create the parent issue first, then clone subtasks under the new parent.
- Write a local creation report with the new Jira keys.
- Stop without creating anything if Jira returns `401 Unauthorized`.

Never invent source ticket content when Jira cannot be read. Ask for credentials, a Jira export, or pasted issue details.

## Epic-Level Clone Under Existing INIT

Use this flow when a team has already created the target quarter INIT and wants to clone only selected Epic-level items under it:

```bash
python scripts/clone_jira_init_epics.py --source-init INIT-12345 --target-init INIT-67890 --quarter 2026Q3 --dry-run
python scripts/clone_jira_init_epics.py --source-init INIT-12345 --target-init INIT-67890 --quarter 2026Q3 --create
```

Rules:

- Use `--dry-run` first and show the operation list.
- Create only to Epic level unless the user explicitly asks for lower-level stories/tasks.
- Inherit fields from the source Epic/template item only when they remain valid for the target quarter.
- Remap quarter-specific fields to the target quarter:
  - Fix Version / fixVersions.
  - Sprint, if your team uses sprint on Epics.
  - Quarter text in summary, description, labels, and custom text fields.
- Filter by configured team/scope before creation.
- Skip cancelled source items by default.
- Skip full-stack or cross-team Epics unless the user explicitly includes them.
- Before creating anything, present source issue, target parent, team, summary, issue type, fix version, sprint, and assumptions.

## Team Scope And Ownership Rules

Use these as generic hygiene rules for INIT/Epic planning. Team-specific values must come from the user's config or prompt.

- Do not decide ownership from the INIT Team field alone when child Epic data exists.
- Treat an INIT as in scope when either condition is true:
  - The INIT Team field includes one of the configured in-scope team values.
  - Any child Epic under the INIT Parent Link has a configured in-scope team value.
- Exclude configured out-of-scope teams when no direct in-scope child Epic exists.
- If a vertical, product track, or portfolio field is populated and conflicts with the configured scope, treat the issue as out of scope unless the user explicitly includes it.
- Ignore configured external projects by default. Do not process them or list them as ambiguous owner items unless the user explicitly includes those projects.
- If the INIT Team is blank but child Epics are clearly in scope, include the INIT in the cleanup list.
- If an INIT has mixed ownership and it is unclear which team owns the work, do not modify it. List it as ambiguous with child Epic evidence and ask for confirmation.
- Treat existing Team values as authoritative.
  - Only auto-fill Team when the Team field is blank and the issue is otherwise clearly in scope.
  - If Team already contains an out-of-scope team, do not overwrite, remove, or append another team unless the user explicitly says to replace or clear that Team.
  - If Team is mixed between in-scope and out-of-scope teams, do not normalize it automatically. Edit only child issues with direct in-scope evidence, or ask before changing ownership-sensitive fields.
  - Do not infer Team from project key, assignee, reporter, or fallback rules when an existing non-blank Team conflicts with that inference. Report it as an ownership conflict.

## Hygiene Cleanup Rules

For hygiene labels such as `NO ESTIMATE`, `NO TARGET DATES`, `WRONG TARGET DATES`, `NO FIX VERSION/S`, `NOT STARTED IN TIME`, `NOT FINISHED IN TIME`, and `NOT ADDRESSED`, fix the underlying source fields instead of trying to edit scripted hygiene fields directly.

Default cleanup posture:

- Do not ignore past-quarter noise just because it is historical. Use the quarters included in the user's query, or ask for the cleanup window.
- Apply ownership rules first. Only process historical items that are clearly in scope or clearly have in-scope child Epics.
- If a historical item is in scope and still appears because fields are missing or inconsistent, fix the source fields that make the report abnormal: assignee, blank Team, target start/end, fix version when required, DEV/QA estimates when a configured estimate rule applies, and committed value when the user asks for committed cleanup.
- If a historical item is already Closed / Resolved / Done but still appears in an anomaly filter, it can still be actionable for field hygiene. Fix missing fields when safe, but do not reopen, cancel, close again, or otherwise transition status unless the user explicitly asks.
- If a historical item appears because it is wrongly associated with an in-scope team, do not clear Team automatically. Treat it as an ownership conflict unless the user explicitly says to remove the team data.
- If the item is outside scope because of external projects, another vertical, or another team's non-empty Team field, do not modify it. Return it as out-of-scope / blocked.

## Default Fix Patterns

Only apply these patterns when the user's team config or prompt provides the concrete values.

- Missing quarter target dates:
  - If target dates are missing or outside the target quarter on confirmed in-scope items, propose the configured quarter window.
  - When either target start or target end is outside the quarter window, set both together so Jira does not reject the update because start becomes later than end.
  - For planning windows that end before calendar quarter end, use the team's configured final delivery date, not a hard-coded global date.
- Missing Fix Version:
  - Add a missing Fix Version only when the quarter and product/release mapping is clear.
  - Preserve existing relevant fix versions unless replacement is required to fix a clear quarter mismatch.
- Missing DEV/QA estimates:
  - Do not invent DEV or QA estimates.
  - Use a ratio rule such as `QA = DEV / 2` only when the user or local config explicitly says that rule applies, QA is blank, and DEV is present.
  - If DEV estimate is empty, list the Epic for owner confirmation.
- Missing assignee:
  - Prefer existing configured owner mapping when explicit.
  - For technical INITs, prefer the INIT reporter only when the reporter is an assignable active user and the team uses reporter-as-owner.
  - If there is one in-scope child Epic assignee, use that as candidate evidence.
  - If multiple assignees exist, list candidate assignees and ask before changing.
- Blank Team:
  - Fill Team only when ownership evidence is clear or the team config provides a safe fallback.
  - Do not overwrite an existing Team value.

## Live Jira Safety Gates

Apply these gates before any live Jira update. Prefer fixing fewer fields correctly over clearing a hygiene filter by changing ownership or status incorrectly.

- Re-read before write. Immediately before every Jira `PUT` or transition, fetch the issue again and compare current Team, status, assignee, target dates, fix versions, DEV estimate, QA estimate, and Parent Link against the planned operation. If a field changed since the scan or dry run, skip that issue and report it as changed during processing.
- Keep non-empty fields unless explicitly told to overwrite. Do not overwrite existing Team, assignee, DEV estimate, QA estimate, target dates, fix versions, Parent Link, Epic Link, labels, or status just because the hygiene filter still shows the issue. Fill blanks and correct clear quarter mismatches only when scope is confirmed.
- Do not clear fields unless the user explicitly asks to clear them. This includes Team, assignee, target dates, fix versions, labels, Parent Link, and Epic Link.
- Status changes are high risk. Do not cancel, close, resolve, reopen, or transition active/initial issues to clear hygiene labels unless the user explicitly asks for that status action on that issue set.
- For status changes, list exact issue keys, current status, target status, and blocking child issues before acting unless the user explicitly says to do it directly.
- Parent/Epic relationship changes are high risk. Do not change Parent Link, Epic Link, or detach/move children to clear hygiene labels unless the user explicitly asks for that relationship change.
- External project guard: default editable child projects must come from config or the user's prompt. Treat unfamiliar project keys as external and skip them unless explicitly included.
- Quarter consistency guard: derive the target quarter from the user request first, then from Jira quarter fields. If the request quarter and issue quarter conflict, stop and report the conflict.
- Fix Version guard: do not replace existing fix versions from another quarter unless the user explicitly says to move the issue to the new quarter or the issue's quarter fields prove the move.
- Estimate guard: do not overwrite non-empty DEV/QA estimates unless the user gives explicit values or says to overwrite.
- Bulk update guard: for more than five issues, or any operation touching Team, status, Parent Link, Epic Link, or external projects, produce a dry-run operation list first unless the user explicitly says to execute directly.
- Hygiene-filter guard: a Jira hygiene flag is not proof that the issue belongs to the user's team. Use Team, vertical/product track, child evidence, project key, and current assignee together. If evidence conflicts, report it as ownership conflict.
- After every live update batch, read back updated issues and report failed, skipped, blocked, or still-flagged items. Do not claim the filter is clean unless a follow-up query confirms it.

## Compliance Scan

Use the read-only scanner when the user asks whether a quarter INIT and its Epics follow the configured rules:

```bash
python scripts/scan_jira_init_compliance.py --init INIT-67890 --quarter 2026Q3 --base-url "$JIRA_BASE_URL" --output-dir ./out
```

The scanner must not modify Jira. It checks:

- The target INIT issue and all Epic issues under its Parent Link.
- In-scope marker presence according to configured team/scope values.
- No Cancelled / Canceled status unless the team allows historical cancelled items.
- No excluded summary patterns unless explicitly included.
- Fix Version values are for the target quarter when the team requires quarter FVs.
- Sprint values are for the target quarter when the team uses sprint on Epics. Report missing Sprint as a warning if the team does not require it.
- Ignore Closed / Resolved / Done Epics for FV/Sprint cleanup unless the user asks to clean historical hygiene fields.
- Ignore configured external projects unless explicitly included.

When Jira authentication is unavailable, do not guess. Report that live scanning is blocked and ask for `JIRA_PAT` or `JIRA_USERNAME` / `JIRA_API_TOKEN`.

## Generator

Run the generator from the skill folder:

```bash
python scripts/generate_quarterly_jira.py --template references/quarterly-templates.json --quarter 2026Q3 --project-key PROJ --output-dir ./out --format all
```

Useful options:

- `--template`: JSON template path.
- `--quarter`: target quarter.
- `--project-key`: overrides template default project key.
- `--output-dir`: folder for generated files.
- `--format`: `json`, `csv`, `md`, or `all`.
- `--var KEY=VALUE`: additional template variable. Repeat as needed.

The generator can write:

- `jira-quarterly-init-<quarter>.json`: structured preview.
- `jira-quarterly-init-<quarter>.md`: human review checklist.
- `jira-quarterly-init-<quarter>.csv`: Jira bulk import friendly table, only when requested.

## Output Expectations

When responding to the user, summarize:

- target quarter and project key used
- source template or target parent used
- number of Epics and tasks generated or scanned
- generated artifact paths
- assumptions or missing fields that need review
- whether anything was created or updated live in Jira
- processed, remaining, blocked, skipped, and ownership-conflict issues
- for any planned or completed Team-field change: current Team, proposed/new Team, and evidence used to decide ownership

Format every user-facing Jira issue key as a clickable Markdown link when a Jira base URL is known, for example `[PROJ-123](https://jira.example.com/browse/PROJ-123)`. Keep raw keys only inside JQL, commands, JSON/CSV imports, code, branch names, or API payloads.

Do not claim Jira issues were created, updated, or cleaned unless the tool/API call actually succeeded and readback verified it. If Jira auth failed, include the exact blocker and the smallest credential/data the user needs to provide.
