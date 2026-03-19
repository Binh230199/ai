---
name: risk-assessment
description: >
  Use when identifying, classifying, and mitigating project risks. Covers the
  full risk management workflow: brainstorming risks across five categories,
  scoring them on a probability × impact matrix, writing proactive mitigation
  strategies, reactive contingency plans, and maintaining a Markdown risk register.
argument-hint: <project name or plan file to assess risks for>
---

# Risk Assessment

Risk assessment ensures that a project team anticipates threats before they
materialize. This skill covers the full lifecycle: identifying risks across
five standard categories, scoring them on a probability × impact matrix to
derive severity, assigning mitigation owners, and maintaining a living
Markdown risk register. Rigorous risk assessment prevents surprise failures
and ensures a contingency is ready when things go wrong.

## When to Use This Skill

- A plan is being created or updated and needs a `## Risks` section populated.
- An existing plan has no or incomplete risk coverage.
- A project milestone is approaching and a formal risk review is needed.
- A new technical, schedule, resource, or external change has been introduced.
- A risk has materialized and the response plan must be activated.
- A stakeholder asks: "What could go wrong and what are we doing about it?"

## Prerequisites

- A clear understanding of the project's goal, scope, and constraints.
- The task list and dependency map from the plan (used to identify schedule risks).
- Knowledge of the technology stack and team capabilities.
- A list of known external dependencies: third-party APIs, vendors, regulations, and cloud services.

## Step-by-Step Workflow

### Step 1: Brainstorm Risks Across All Five Categories

Generate risks by systematically scanning each category. Target at least 2–3 risks per category.

| Category     | Example Risks to Consider |
|--------------|---------------------------|
| **Schedule** | Key engineer unavailable; dependency arrives late; task durations underestimated |
| **Technical**| Third-party API breaking change; chosen library lacks a needed feature; performance bottleneck |
| **Resource** | Budget reduction; team member departure; required hardware unavailable |
| **External** | Regulatory change; customer requirement change mid-project; vendor discontinues a service |
| **Quality**  | Insufficient test coverage; integration failures discovered late; undetected security vulnerability |

**Brainstorming techniques:**

- **Assumption inversion**: List every assumption the plan makes, then invert it.
  Example: "We assume the payment API is stable" → Risk: "Payment API deprecates the v2 endpoints mid-development."
- **Pre-mortem**: Imagine the project failed — what went wrong? List those causes as risks.
- **Dependency scan**: Review every external dependency in the task list. Each one is a potential risk source.

### Step 2: Classify Risks with a Probability × Impact Matrix

Score each risk independently on two dimensions:

- **Probability**: How likely is this to occur? (Low / Medium / High)
- **Impact**: How severe would the consequence be if it occurs? (Low / Medium / High)

Derive **Severity** using this matrix:

|                       | **Low Impact** | **Medium Impact** | **High Impact** |
|-----------------------|---------------|-------------------|-----------------|
| **High Probability**  | Medium        | High              | High            |
| **Medium Probability**| Low           | Medium            | High            |
| **Low Probability**   | Low           | Low               | Medium          |

**Severity response levels:**
- **High**: Requires a mitigation plan, a contingency plan, and weekly monitoring.
- **Medium**: Requires a mitigation plan and bi-weekly check.
- **Low**: Document and monitor monthly; accept if mitigation cost exceeds probable impact.

### Step 3: Write Mitigation Plans

For every risk with severity **Medium** or **High**, write an explicit mitigation strategy. A mitigation:

- Is a **proactive action** that reduces probability or impact **before** the risk occurs.
- Names an **owner** role responsible for executing it.
- Is stated in one concrete action sentence.

**Template:**
> "To reduce the [likelihood/impact] of [risk], [owner] will [specific action] by [date or milestone]."

**Examples:**
- "To reduce the likelihood of API breakage, DevOps will pin the third-party API to a specific version tag and add changelog monitoring by Sprint 1."
- "To reduce the impact of a key engineer being unavailable, the Tech Lead will ensure all critical modules have a second engineer who has reviewed the code by the end of Sprint 2."

### Step 4: Write Contingency Plans

A contingency plan is the **reactive response** executed if the risk materializes despite mitigation. It answers: "If this happens, what do we do next?"

**Template:**
> "If [risk event] occurs, [owner] will [specific response action], targeting [recovery outcome] within [timeframe]."

**Examples:**
- "If the auth API breaks in production, DevOps will activate the cached fallback endpoint and the Backend Dev will evaluate migration to the backup provider within 2 business days."
- "If the key engineer is unavailable for more than 3 days, the Project Lead will redistribute tasks T07–T10 to the secondary engineer per the pre-agreed contingency assignments."

### Step 5: Format the Risk Register

Document all risks in the standard Markdown risk register table:

```markdown
## Risks

| ID  | Category  | Risk Description                                   | Probability | Impact | Severity | Mitigation                                                | Owner       |
|-----|-----------|----------------------------------------------------|-------------|--------|----------|-----------------------------------------------------------|-------------|
| R01 | Technical | Third-party auth API breaking change breaks /login | Medium      | High   | High     | Pin API to v2.3.1; monitor changelog weekly               | DevOps      |
| R02 | Schedule  | Integration test phase underestimated, delays ship | High        | Medium | High     | Add 20% buffer to test estimates; daily standups in S3    | Tech Lead   |
| R03 | Resource  | Key backend engineer unavailable during Sprint 2  | Low         | High   | Medium   | Cross-train secondary engineer on auth module by end S1   | Tech Lead   |
| R04 | External  | Security vulnerability in JWT library              | Low         | High   | Medium   | Subscribe to CVE alerts; monthly dependency review        | Backend Dev |
| R05 | Quality   | Insufficient coverage leads to production bug     | Medium      | Medium | Medium   | Enforce 80% coverage gate in CI; QA review pre-deploy     | QA Engineer |
```

**Column rules:**
- `ID`: Sequential, prefix `R` + zero-padded two-digit number: `R01`, `R02`.
- `Category`: ONE of: `Schedule`, `Technical`, `Resource`, `External`, `Quality`.
- `Probability`, `Impact`, `Severity`: Each must be `Low`, `Medium`, or `High`.
- `Mitigation`: Required for Medium and High severity. One action sentence.
- `Owner`: Role title. Never `TBD`.

### Step 6: Prioritize and Schedule Reviews

1. Sort the risk register by Severity descending (High first, then Medium, then Low).
2. For every High-severity risk, verify both a mitigation and contingency plan exist.
3. Assign a review cadence: High = weekly, Medium = bi-weekly, Low = monthly.
4. Add a "Risk Review" milestone to the plan's `## Milestones` section with the first review date.

## Examples

### Good Pattern — Complete Risk Register Entry

```markdown
| R01 | Technical | Third-party auth API breaking change breaks /login | Medium | High | High | Pin API to v2.3.1; monitor changelog weekly | DevOps |
```

- Risk is specific and linked to a concrete technical decision.
- Probability and Impact are independently scored (not both defaulted to High).
- Severity is correctly derived: Medium probability × High impact = **High**.
- Mitigation is proactive — a specific version pin and changelog subscription.
- Owner is a named role, not "TBD".

### Bad Pattern — Incomplete Risk Register Entry

```markdown
| R01 | General | Something could go wrong with the API | High | High | High | Monitor it | TBD |
```

Problems:
- "Something could go wrong" is not actionable — the team cannot mitigate a vague risk.
- "Monitor it" is observation, not mitigation.
- Owner is "TBD" — nobody will act on this.
- Both Probability and Impact defaulted to High without analysis.

**Fix**: Name the specific API, state the specific failure mode, write a precise proactive action with a target date, and assign a named owner role.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Risk register has "TBD" in mitigation columns | Risk identified but not analyzed | Block plan finalization until every High-severity risk has a completed mitigation row |
| All risks rated High severity | Matrix not applied consistently | Re-score each risk independently; Low-probability events are rarely High severity |
| Same risk listed twice | Brainstorming produced duplicates | Merge duplicates; distinguish by failure mode only if they are genuinely different scenarios |
| Mitigation strategies are vague ("monitor closely") | Owner has not committed to a specific action | Rewrite each mitigation as: action verb + specific artifact + owner + deadline |
| Risk register never updated after initial creation | No review cadence established | Add a recurring "Risk Review" milestone to the plan with a specific date |

## References

- ISO 31000:2018 — Risk Management Guidelines.
- PMI PMBOK Guide, 7th Edition, Chapter 11 — Project Risk Management.
- OWASP Risk Rating Methodology (for software-specific technical risks): https://owasp.org/www-community/OWASP_Risk_Rating_Methodology
