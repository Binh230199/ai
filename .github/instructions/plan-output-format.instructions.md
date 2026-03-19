---
name: 'Plan Output Format'
description: 'Enforces consistent YAML front-matter, heading structure, and table formatting in all plan Markdown documents'
applyTo: '**/*.md'
---

# Plan Document Formatting Standards

## YAML Front-Matter Rules

- Every plan document MUST begin with a YAML front-matter block delimited by `---` on the first line.
- The following four fields are REQUIRED in every plan document's front-matter:
  - `title`: A concise, human-readable name for the plan (string, no special characters).
  - `date`: The creation or last-updated date in `YYYY-MM-DD` format.
  - `status`: The current rollup status. MUST be exactly one of: `not-started`, `in-progress`, `done`, `blocked`.
  - `owner`: The name or role of the person responsible for this plan.
- Optional front-matter fields include: `deadline`, `version`, `reviewers`. They MUST also use `YYYY-MM-DD` for any date value.
- Front-matter MUST be the very first content in the file — no blank lines or text may appear before the opening `---`.

## Heading Structure Rules

- The document MUST begin with a single H1 (`#`) heading immediately after the closing `---` of the front-matter. This heading is the plan title and MUST match the `title` field exactly.
- The following H2 (`##`) sections are REQUIRED and MUST appear in this exact order:
  1. `## Goal`
  2. `## Tasks`
  3. `## Dependencies`
  4. `## Milestones`
  5. `## Risks`
- No required H2 section may be omitted. If a section has no content yet, write `_Not yet assessed._` as the body text.
- H3 (`###`) and deeper headings are optional and may be used freely within sections.
- Do NOT use H1 headings anywhere in the document other than the plan title.

## Task Table Rules

- All tasks MUST be presented as a Markdown table in the `## Tasks` section.
- Required columns, in this exact order: `ID`, `Task`, `Owner`, `Duration`, `Status`, `Depends On`.
- `ID` values MUST follow the format `T` + zero-padded two-digit number: `T01`, `T02`, `T10`, `T15`.
- `Status` values MUST be exactly one of: `not-started`, `in-progress`, `done`, `blocked`. No other values are permitted.
- `Duration` MUST include a unit suffix: `h` for hours or `d` for days (e.g., `2h`, `0.5d`, `3d`).
- The `Depends On` column MUST contain either a comma-separated list of existing task IDs or the em-dash character `—` if there are no dependencies.
- Every task ID referenced in `Depends On` MUST exist as a row in the same task table.

## Dependency Diagram Rules

- The `## Dependencies` section MUST contain a fenced Mermaid code block using `flowchart TD`.
- Every task node shown in the diagram MUST correspond to a task ID in the `## Tasks` table.
- Each node label MUST use this format: `ID["ID: Short task name"]`.
- Edges MUST use the `-->` directed arrow. Do NOT use `---` (undirected) edges.
- Immediately below the diagram fenced block, include a `**Critical Path**:` line listing the critical path task IDs in sequence, e.g.: `**Critical Path**: T01 → T02 → T05 → T07`

## Risk Table Rules

- All risks MUST be presented as a Markdown table in the `## Risks` section.
- Required columns, in this exact order: `ID`, `Category`, `Risk Description`, `Probability`, `Impact`, `Severity`, `Mitigation`, `Owner`.
- `ID` values MUST follow the format `R` + zero-padded two-digit number: `R01`, `R02`.
- `Category` MUST be exactly one of: `Schedule`, `Technical`, `Resource`, `External`, `Quality`.
- `Probability`, `Impact`, and `Severity` MUST each be exactly one of: `Low`, `Medium`, `High`.
- Every risk row with `Severity` equal to `High` MUST have a non-empty `Mitigation` cell that describes a specific proactive action.

## Milestone Table Rules

- All milestones MUST be presented as a Markdown table in the `## Milestones` section.
- Required columns: `Milestone`, `Target Date`, `Tasks Included`.
- `Target Date` MUST use `YYYY-MM-DD` format.
- `Tasks Included` MUST list the task IDs (comma-separated) that must be `done` before this milestone is considered reached.

## General Formatting Rules

- Do NOT use raw HTML inside plan documents. Use only Markdown syntax.
- Do NOT use emoji in headings or table cells.
- When referencing a task ID in prose, wrap it in inline code backticks: "task `T03` depends on `T01`".
- All Markdown tables MUST have a header row immediately followed by a separator row (pipes and hyphens with no text: `|---|---|`).
- A blank line MUST appear before and after every heading, table, and fenced code block.
- The `status` field value in front-matter MUST reflect the aggregate state of the plan's tasks — if any task is `blocked`, the plan status MUST be `blocked`.
