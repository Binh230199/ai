# Design Procedure

Use this procedure when designing an agentic AI system.

## 1. Normalize the Brief

Turn the request into:

- objective
- scope
- inputs
- constraints
- integrations
- completion criteria
- deliverables

Do not start architecture work until these are explicit enough to drive tradeoffs.

## 2. Define the System Layers

Every serious agentic system should be modeled across these planes:

- control plane: orchestration, queueing, ownership, retries, closure
- execution plane: specialist agents and worker boundaries
- knowledge plane: instructions, skills, references, templates, memory artifacts
- policy plane: hooks, approvals, verification gates, safety controls
- integration plane: MCP, APIs, shell commands, test tools, external platforms
- recovery plane: manifests, checkpoints, retries, resume logic, final reconciliation

## 3. Design the Phase Flow

Use a phase flow rather than a flat task list. A strong default is:

1. intake
2. partition
3. research
4. implementation
5. verification
6. reconciliation
7. closeout

If the target workflow is read-only, you may compress or remove implementation.

## 4. Assign Narrow Roles

At minimum, consider these roles:

- orchestrator
- analyst or researcher
- implementer or writer
- verifier
- packager

Only combine roles when the workflow is simple enough that separation would add more cost than safety.

## 5. Externalize Runtime State

Never rely on chat history alone for long-running work. Specify artifacts such as:

- manifest.json
- batches.json or per-batch files
- runbook.md
- touched-files.json
- uncovered.json
- final-report.md

Make it possible to stop and resume without losing progress.

## 6. Map to Copilot Primitives

Choose the right file type for each concern:

- workspace instructions for universal workspace rules
- file instructions for domain-specific or file-scoped rules
- prompts for single entrypoints
- agents for specialist roles and tool restrictions
- skills for reusable procedures and references
- hooks for deterministic validation or enforcement

## 7. Add Verification and Recovery

The design is incomplete unless it states:

- what evidence proves completion
- who verifies it
- what happens when a batch fails
- how the system resumes after interruption

## 8. Review for Cost and Latency

Explicitly optimize:

- which phases can run in parallel
- where context should be narrowed
- what should live in artifacts rather than chat
- what knowledge should move into a skill or reference doc
