# Worked Example: Designing a Multi-Stage Engineering Automation System

Use this example when the target system needs a concrete reference design without anchoring the factory to one specific domain.

## Example Objective

Design a GitHub Copilot-based agentic system that can:

- intake a structured engineering objective
- analyze the relevant repository and infrastructure context
- partition work into manageable batches or phases
- coordinate specialist agents for research, implementation, and verification
- persist runtime state in artifacts
- continue until explicit completion criteria are satisfied

## Recommended Roles

- `orchestrator`: owns the manifest, role assignment, and closure logic
- `requirements-analyst`: normalizes the brief and identifies missing inputs
- `workflow-architect`: defines the phase flow, artifacts, and recovery logic
- `integration-architect`: specifies integrations, hooks, and runtime contracts
- `copilot-bundle-architect`: maps the design into Copilot customization files
- `quality-governor`: checks for weak verification, vague completion, and operational gaps
- `system-packager`: materializes the approved bundle

## Recommended Artifacts

- `artifacts/<system-name>/manifest.json`
- `artifacts/<system-name>/runbook.md`
- `artifacts/<system-name>/batches/`
- `artifacts/<system-name>/reviews/`
- `artifacts/<system-name>/final-report.md`

## Key Design Decisions

- Use a manifest-driven workflow, not a loose task list.
- Separate design, packaging, and review responsibilities.
- Keep roles narrow and contexts small.
- Use hooks for deterministic validation where failure would be costly.
- Treat interruption and resumption as first-class requirements.

## Completion Criteria Example

- the design brief is complete and internally consistent
- the agent matrix, bundle map, artifacts, and recovery logic are specified
- verification and completion gates are explicit
- rollout guidance is concrete enough to implement

## Why This Example Matters

It demonstrates that the factory should produce systems with:

- structured objectives
- evidence-based completion
- clear role boundaries
- reusable Copilot customizations
- recovery-aware execution models