# Quarterly Jira Template Schema

Use `quarterly-templates.json` as the durable team template. The file should be valid JSON.

## Top-Level Shape

```json
{
  "defaults": {
    "project_key": "PROJ",
    "issue_type_names": {
      "epic": "Epic",
      "task": "Task"
    },
    "labels": ["quarterly-init"],
    "components": ["Planning"],
    "priority": "Medium"
  },
  "epics": [
    {
      "id": "example-epic",
      "summary": "{{quarter_human}} Example Init",
      "epic_name": "{{quarter_human}} Example Init",
      "description": "Purpose and acceptance criteria.",
      "tasks": [
        {
          "id": "example-task",
          "summary": "{{quarter_human}} Example Task",
          "description": "Task details."
        }
      ]
    }
  ]
}
```

## Supported Template Tokens

- `{{quarter}}`: compact quarter, for example `2026Q3`
- `{{quarter_human}}`: readable quarter, for example `Q3 2026`
- `{{quarter_slug}}`: filesystem-friendly quarter, for example `2026-q3`
- `{{year}}`: year, for example `2026`
- `{{quarter_number}}`: quarter number, for example `3`
- `{{quarter_start}}`: calendar quarter start date, ISO format
- `{{quarter_end}}`: calendar quarter end date, ISO format
- `{{project_key}}`: Jira project key
- any custom `--var KEY=VALUE` value passed to the generator

## Epic Fields

Recommended fields:

- `id`: stable template ID, lowercase hyphenated
- `summary`
- `epic_name`
- `description`
- `labels`
- `components`
- `priority`
- `assignee`
- `story_points`
- `due_date`
- `fields`: object for custom Jira fields
- `tasks`: child issue templates

## Task Fields

Recommended fields:

- `id`: stable template ID within its epic
- `issue_type`: defaults to task issue type
- `summary`
- `description`
- `labels`
- `components`
- `priority`
- `assignee`
- `story_points`
- `due_date`
- `fields`: object for custom Jira fields

## Notes

- Use template IDs that remain stable across quarters; generated external IDs are derived from them.
- Keep generated content reviewable. Avoid embedding secrets, customer data, or one-off incident details in the skill.
- Jira custom fields vary by instance. Put them under `fields` and map them during bulk import or API creation.
