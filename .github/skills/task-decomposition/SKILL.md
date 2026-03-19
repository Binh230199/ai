---
name: task-decomposition
description: >
  Use when breaking a complex goal or project requirement into atomic, measurable,
  assignable tasks. Covers the full SMART decomposition workflow: understanding the
  goal, identifying deliverables, creating work packages, assigning ownership and
  duration, and validating completeness. Applies to software projects, planning
  agents, and any structured task list creation.
argument-hint: <goal or deliverable to decompose>
---

# Task Decomposition

Task decomposition is the process of taking a high-level goal and breaking it
down into discrete, independently executable units of work. Each resulting task
must satisfy the **SMART criteria**: Specific, Measurable, Assignable, Relevant,
and Time-bound. Well-decomposed tasks are the foundation of accurate scheduling,
clear ownership, and reliable delivery tracking.

## When to Use This Skill

- A goal statement or requirement needs to be turned into an actionable task list.
- A deliverable is too large or vague to be assigned to a single person.
- A sprint or milestone plan needs to be populated with concrete work items.
- An existing plan has tasks that are poorly scoped or overlap with each other.
- You need to produce the `## Tasks` section of a plan document.
- A team member asks: "What exactly do we need to do to achieve this?"

## Prerequisites

- A written goal statement (rough draft is acceptable).
- Knowledge of the team's roles and approximate available capacity.
- Understanding of the technology or domain involved — enough to name realistic tasks.
- Access to any existing requirements documents, architecture diagrams, or previous plans.

## Step-by-Step Workflow

### Step 1: Understand and Restate the Goal

Read the goal statement carefully. Rewrite it in your own words, structured as:

- **Objective**: What must be achieved?
- **Success Criteria**: How will we know it is done?
- **Constraints**: What are the non-negotiable boundaries (deadline, technology, team size)?

**Example restatement:**

> **Goal**: Build a REST API service for user authentication.
> **Objective**: Deliver a production-ready REST API handling user registration, login, token refresh, and logout.
> **Success Criteria**: All four endpoints return correct HTTP status codes, pass the agreed integration test suite, and are deployed to staging.
> **Constraints**: Must use Node.js + Express, deliver within 3 weeks, team of 2 engineers.

### Step 2: Identify Top-Level Deliverables

List the major deliverables — the tangible outputs that together constitute the goal being complete. Aim for 3–7 deliverables per goal.

**Technique — Noun decomposition**: Ask "What artifacts, systems, or documents must exist when this is done?"

| Deliverable              | Description                                              |
|--------------------------|----------------------------------------------------------|
| API service codebase     | Node.js/Express app with all four endpoints implemented  |
| Authentication middleware| JWT validation logic as reusable middleware              |
| Database schema          | User table with password hash and token fields           |
| Integration test suite   | Automated tests for all endpoints and error cases        |
| Deployment configuration | Docker Compose + CI pipeline to staging                  |

### Step 3: Break Each Deliverable into Atomic Work Packages

For each deliverable, ask: "What is the smallest unit of work a single person can complete in one session?" Split until every item:

- Can be completed by ONE person.
- Has a clear done condition.
- Has a realistic duration of 30 minutes to 2 days.
- Does not contain implicit hidden sub-tasks.

**Anti-pattern to avoid**: "Implement authentication" is NOT atomic.

**Correct decomposition:**

| ID  | Task                                              | Owner       | Duration |
|-----|---------------------------------------------------|-------------|----------|
| T01 | Design POST /register request/response schema     | Backend Dev | 2h       |
| T02 | Implement POST /register endpoint with validation | Backend Dev | 4h       |
| T03 | Write unit tests for POST /register               | Backend Dev | 2h       |

### Step 4: Apply SMART Criteria to Each Task

For every task, verify all five SMART dimensions:

| Dimension      | Question to Ask                                  | Fix if Failing                             |
|----------------|--------------------------------------------------|--------------------------------------------|
| **Specific**   | Is it clear exactly what work is done?           | Add the "what" and "how" explicitly        |
| **Measurable** | Is there a concrete done condition?              | Add acceptance criteria or a test          |
| **Assignable** | Can one person own this?                         | Split if multiple roles are needed         |
| **Relevant**   | Does it contribute directly to the goal?         | Remove or merge trivial tasks              |
| **Time-bound** | Does it have a duration estimate?                | Add estimate in hours (`h`) or days (`d`)  |

### Step 5: Format Tasks in the Standard Task Table

Output all tasks as a Markdown table with these exact columns:

```markdown
| ID  | Task                                          | Owner       | Duration | Status      | Depends On |
|-----|-----------------------------------------------|-------------|----------|-------------|------------|
| T01 | Design POST /register request/response schema | Backend Dev | 2h       | not-started | —          |
| T02 | Implement POST /register endpoint             | Backend Dev | 4h       | not-started | T01        |
| T03 | Write unit tests for POST /register           | Backend Dev | 2h       | not-started | T02        |
| T04 | Design POST /login schema                     | Backend Dev | 1h       | not-started | T01        |
| T05 | Implement POST /login endpoint + JWT issuance | Backend Dev | 4h       | not-started | T04        |
```

**Column rules:**
- `ID`: Sequential, prefix `T` + zero-padded two-digit number: `T01`, `T02`, `T10`.
- `Task`: Verb + noun phrase. Start with an action word: Design, Implement, Write, Configure, Deploy, Review, Test.
- `Owner`: Role title, not a person's name (Backend Dev, QA Engineer, DevOps).
- `Duration`: Always include unit suffix — `h` for hours, `d` for days (e.g., `2h`, `0.5d`, `3d`).
- `Status`: ONE of: `not-started`, `in-progress`, `done`, `blocked`.
- `Depends On`: Comma-separated task IDs, or em-dash `—` if none.

### Step 6: Validate Completeness

Before finalizing, run this checklist:

- [ ] Every deliverable from Step 2 has at least one task assigned to it.
- [ ] No task has a duration estimate over 5 days — split further if so.
- [ ] No two tasks have identical or overlapping scope.
- [ ] Every task has a unique ID with no gaps in the sequence.
- [ ] All `Depends On` references point to existing task IDs in the same table.
- [ ] The task list, if executed in dependency order, would fully deliver the stated goal.

## Examples

### Good Pattern — Atomic, SMART Task

```markdown
| T07 | Configure Dockerfile for Node.js API service | DevOps | 3h | not-started | T06 |
```

- **Specific**: Exactly what is being configured (Dockerfile, Node.js API service).
- **Measurable**: Done when `docker build` succeeds locally and image starts correctly.
- **Assignable**: DevOps owns it exclusively.
- **Relevant**: Required for the deployment pipeline deliverable.
- **Time-bound**: 3 hours.

### Bad Pattern — Vague, Non-atomic Task

```markdown
| T07 | Set up infrastructure | DevOps | 2w | not-started | T06 |
```

Problems:
- "Set up infrastructure" could mean 20 different things.
- 2 weeks is too long — no visibility into daily progress.
- No done condition defined.
- Untestable in a standup.

**Fix**: Split into separate rows — configure Dockerfile (3h), write docker-compose.yml (2h), configure CI pipeline (4h), provision staging server (2h), write deployment runbook (2h).

### Good Pattern — Complete Task Table

```markdown
| ID  | Task                                    | Owner       | Duration | Status      | Depends On |
|-----|-----------------------------------------|-------------|----------|-------------|------------|
| T01 | Write OpenAPI spec for all 4 endpoints  | Backend Dev | 4h       | not-started | —          |
| T02 | Scaffold Express app + folder structure | Backend Dev | 2h       | not-started | T01        |
| T03 | Implement POST /register                | Backend Dev | 4h       | in-progress | T02        |
| T04 | Write integration tests for /register   | QA Engineer | 3h       | not-started | T03        |
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Tasks keep growing in scope during execution | Insufficient decomposition in Step 3 | Re-apply Step 3: ask "is this one person, one session?" — split if no |
| Cannot assign an owner because multiple teams are needed | Task spans team boundaries | Split at the team boundary; add a handoff or integration task |
| Duration estimates are constantly wrong | Tasks are not specific enough | Add explicit done conditions (acceptance criteria) to each task |
| Task list misses critical work | Deliverables not fully enumerated in Step 2 | Re-run Step 2 with domain experts; ask "what else must exist when we're done?" |
| ID references in "Depends On" don't exist | Tasks were renumbered after editing | Renumber sequentially after all tasks are finalized; use find-replace for IDs |

## References

- SMART criteria: Doran, G.T. (1981). "There's a S.M.A.R.T. way to write management's goals and objectives." — *Management Review* 70(11).
- Work Breakdown Structure (WBS): PMI PMBOK Guide, 7th Edition, Section 5.4.
- Agile task sizing: Mike Cohn, *Agile Estimating and Planning*, Chapter 5.
