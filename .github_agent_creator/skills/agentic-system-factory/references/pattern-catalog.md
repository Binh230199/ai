# Pattern Catalog

Use these patterns when designing reliable Copilot-based agentic systems.

## 1. Meta-Orchestrator Pattern

One orchestrator owns the objective, batches, and closure logic. Specialist agents do the actual analysis and writing.

Use when:

- the workflow spans multiple phases
- completion depends on reconciliation across outputs

Avoid when:

- the task is small enough for one prompt and one answer

## 2. Manifest-Driven Execution Pattern

Represent the work as a manifest with explicit status fields, ownership, and evidence.

Benefits:

- resumability
- auditability
- less self-deception from the model

## 3. Research-Before-Write Pattern

Create a research or strategy phase before any high-risk edits.

Benefits:

- better fixes
- lower regression risk
- tighter contexts for writer agents

## 4. Verifier Gate Pattern

The writer is not the verifier. Completion requires independent verification or deterministic hooks.

Benefits:

- fewer false positives
- stronger closure criteria

## 5. Packager Separation Pattern

Use a packager role to materialize the final files after the architecture is reviewed.

Benefits:

- cleaner separation between design and synthesis
- fewer mid-stream architecture drifts

## 6. Artifact Handoff Pattern

Pass artifacts between agents instead of replaying the entire conversation.

Examples:

- manifest.json
- batch spec
- uncovered.json
- final review findings

## 7. Hook Validator Pattern

Use hooks to validate the bundle or the last edit rather than trusting model memory.

Best for:

- customization file validation
- post-edit guardrails
- stop-time summaries

## 8. Cost-Aware Context Partitioning Pattern

Each role should see only what it needs:

- analysts see the brief and repo context
- writers see a narrow implementation spec
- verifiers see the changed scope and verification commands

## 9. Scenario Skill Pattern

Move repeated domain playbooks into skills with references and templates.

Best for:

- domain-specific automation workflows
- verification-heavy engineering programs
- multi-stage operational procedures

## 10. Resume-First Batch Pattern

Design every multi-batch workflow so a new session can continue without reconstructing implicit state.

Required ingredients:

- manifest
- runbook
- per-batch results
- final reconciliation logic
