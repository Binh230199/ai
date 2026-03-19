---
name: breakdown-task
description: 'Decompose a single task into atomic subtasks with time estimates'
argument-hint: <task description and maximum number of subtasks>
agent: planner
tools:
  - read_file
  - create_file
  - search
---

# Break Down a Task into Atomic Subtasks

Decompose the following task into the smallest independently executable subtasks,
each satisfying all five SMART criteria.

**Task to decompose**: ${input:task:Describe the task to decompose}
**Maximum subtasks**: ${input:max_subtasks:Maximum number of subtasks (e.g. 10)}

## Instructions

Apply the [task-decomposition skill](../skills/task-decomposition/SKILL.md) to the task provided:

1. **Restate the task** as a structured objective:
   - **Objective**: What must the task deliver?
   - **Done Condition**: How will we know the task is fully complete?

2. **Identify deliverables**: List every artifact, output, or state change that the task must produce.

3. **Create work packages**: For each deliverable, break it into atomic units of work where each unit:
   - Can be completed by one person in one session (30 minutes to 2 days maximum).
   - Has a clear, testable done state.
   - Does not contain hidden sub-steps.

4. **Verify SMART criteria** for every subtask:
   - **Specific**: The subtask name is a verb + noun phrase with no ambiguity.
   - **Measurable**: A done condition is either explicit in the name or derivable from it.
   - **Assignable**: One owner role is named.
   - **Relevant**: Directly produces a deliverable of the parent task.
   - **Time-bound**: Duration estimate is given in `h` (hours) or `d` (days).

5. **Assign IDs**: Use sequential IDs starting from `ST01`. Do not skip numbers.

6. **Map subtask dependencies**: Fill the `Depends On` column — use `—` for subtasks with no predecessor, or list the comma-separated `ST` IDs that must complete first.

7. **Respect the limit**: Stop at `${input:max_subtasks:Maximum number of subtasks (e.g. 10)}` subtasks. If the task could be broken further, list which subtask IDs are candidates for a follow-up `/breakdown-task` call.

## Output Format

```markdown
## Subtask Breakdown: <Parent Task Name>

**Parent Task**: <Original task description as provided>
**Done Condition**: <One sentence — how we know the parent task is fully complete>

| ID   | Subtask                                  | Owner       | Duration | Status      | Depends On |
|------|------------------------------------------|-------------|----------|-------------|------------|
| ST01 | <Action verb + specific deliverable>     | <Role>      | <Xh/Xd>  | not-started | —          |
| ST02 | <Action verb + specific deliverable>     | <Role>      | <Xh/Xd>  | not-started | ST01       |

**Total Estimated Duration (critical path)**: <sum of durations along the longest dependency chain>

**Subtasks eligible for further decomposition**: <comma-separated ST IDs, or "None — all subtasks are already atomic">
```

## Quality Checklist

Before responding, verify:

- [ ] The number of subtask rows does not exceed the requested maximum.
- [ ] Every subtask name starts with an action verb (Implement, Write, Configure, Design, Review, Deploy, Test, Verify).
- [ ] No subtask has a duration estimate greater than `2d` (16h). Split further if any do.
- [ ] Every subtask has a unique `ST` ID with sequential numbering.
- [ ] Every `Depends On` value references only existing `ST` IDs from this breakdown.
- [ ] All `Status` values are `not-started`.
- [ ] The total estimated duration (critical path) is stated at the bottom.
