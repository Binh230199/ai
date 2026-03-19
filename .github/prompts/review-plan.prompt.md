---
name: review-plan
description: 'Review an existing plan for gaps, risks, and improvements'
argument-hint: <path to the plan file to review>
agent: planner
tools:
  - read_file
  - replace_string_in_file
  - search
---

# Review an Existing Plan

Load and critically review the plan document below, then produce a structured
critique report with concrete, actionable recommendations.

**Plan file**: ${input:plan_file:Path to the plan file to review}

## Instructions

1. **Load the plan file** using `read_file` with the path `${input:plan_file:Path to the plan file to review}`. If the file is not found, immediately report: "Error: File not found. Please provide a correct file path." and stop.

2. **Audit document format** against the [plan-output-format instructions](../instructions/plan-output-format.instructions.md):
   - Verify YAML front-matter has all four required fields: `title`, `date`, `status`, `owner`.
   - Verify all five H2 sections are present in order: Goal, Tasks, Dependencies, Milestones, Risks.
   - Report every missing field or section as a High-severity format issue.

3. **Audit the task list** using the [task-decomposition skill](../skills/task-decomposition/SKILL.md):
   - Flag tasks with no owner or no duration as High severity.
   - Flag tasks with duration > 5 days as Medium severity (likely need further decomposition).
   - Flag tasks that are too vague (no action verb, no measurable done state) as Medium severity.
   - Identify logical work that must exist for the goal but is absent from the task list.

4. **Audit dependencies** using the [dependency-mapping skill](../skills/dependency-mapping/SKILL.md):
   - Check that all `Depends On` IDs exist in the task table. Any orphan reference is High severity.
   - Identify task pairs where a logical hard dependency exists but is not captured.
   - Check the Mermaid diagram for consistency with the task table.

5. **Audit the risk register** using the [risk-assessment skill](../skills/risk-assessment/SKILL.md):
   - Apply the five-category brainstorm (Schedule, Technical, Resource, External, Quality) to the plan. Identify risk categories with no coverage.
   - Flag every High-severity risk row that has an empty Mitigation cell as High severity.
   - Flag any risk with no owner as Medium severity.

6. **Assess timeline realism**:
   - Identify the critical path by examining the `Depends On` relationships and duration estimates.
   - Sum the critical path duration in days.
   - Compare to the `deadline` field in front-matter (if present) or the latest milestone target date.
   - Classify: Realistic (≥20% slack), Tight (<20% slack), or Unrealistic (critical path exceeds deadline).

7. **Compile and output the review report** in the format below.

## Output Format

```markdown
# Plan Review: <Plan Title from front-matter>

**Reviewed file**: `<plan_file>`
**Review date**: <today in YYYY-MM-DD>
**Overall assessment**: PASS | NEEDS REVISION | BLOCKED

> **PASS**: Zero High-severity findings.
> **NEEDS REVISION**: One or more Medium-severity findings, no High.
> **BLOCKED**: One or more High-severity findings — plan cannot be executed as-is.

---

## Format Issues

_Issues with YAML front-matter or required heading structure._

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| <finding> | High/Medium/Low | <specific action to fix> |

_If no issues: "No format issues found."_

## Task Gaps

_Tasks that are missing, vague, have no owner, or are too large._

| Finding | Affected Task | Severity | Recommendation |
|---------|--------------|----------|----------------|
| <finding> | <T-ID or "Missing"> | High/Medium/Low | <specific action> |

_If no issues: "No task gaps found."_

## Dependency Issues

_Missing or incorrect dependency relationships._

| Finding | Affected Tasks | Severity | Recommendation |
|---------|----------------|----------|----------------|
| <finding> | <T-IDs> | High/Medium/Low | <specific action> |

_If no issues: "No dependency issues found."_

## Missing or Incomplete Risks

_Risk categories with no coverage or High-severity risks missing mitigation._

| Risk Category | Gap Description | Severity | Recommended Entry |
|---|---|---|---|
| <category> | <what is missing> | High/Medium/Low | <specific risk to add with mitigation> |

_If no issues: "Risk register appears complete for this project scope."_

## Timeline Assessment

- **Critical path tasks**: <T01 → T02 → ... (list)>
- **Critical path total**: <X days>
- **Deadline / latest milestone**: <YYYY-MM-DD from plan>
- **Available slack**: <N days>
- **Assessment**: Realistic | Tight | Unrealistic
- **Rationale**: <One sentence explaining the assessment.>

## Milestone Gaps

_Milestones with wrong dates, missing task coverage, or milestone sections absent._

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| <finding> | High/Medium/Low | <specific action> |

_If no issues: "Milestone table is complete and consistent."_

## Prioritized Recommendations

Address in order — High severity first:

1. **[High]** <Most critical issue> — <precisely what to do to fix it>
2. **[Medium]** <Second issue> — <precisely what to do>
3. **[Low]** <Third issue> — <precisely what to do>
```

## Quality Checklist

Before responding, verify:

- [ ] The plan file was successfully loaded. If not, the error is clearly reported and no further analysis is attempted.
- [ ] All seven review sections appear in the output, even if their body is "No issues found."
- [ ] Every finding has a concrete recommendation — not "consider improving" but a specific action.
- [ ] The Timeline Assessment includes the exact critical path duration in days.
- [ ] Overall assessment is `PASS` only if there are zero High-severity findings across all sections.
- [ ] No placeholder text, `TODO`, or `...` appears in the review report.
