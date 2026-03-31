---
description: "Use when designing agentic AI systems, multi-agent workflows, Copilot automation systems, engineering orchestration, or autonomous task-completion architectures."
---

# Agentic System Design Rules

- Start with a design brief: objective, scope, inputs, constraints, integrations, risks, exit criteria.
- Model the system in layers: control plane, execution plane, knowledge plane, policy plane, integration plane, and recovery plane.
- Define specialized roles instead of one overloaded agent.
- Encode completion as evidence-backed criteria, not as subjective satisfaction.
- Design runtime artifacts explicitly: manifests, ledgers, runbooks, summaries, and final reports.
- Design for interruption and resumption. Every long-running workflow needs checkpoints and a resume path.
- Make token efficiency an architectural concern: narrow contexts, role-specific inputs, structured artifacts, and reusable skills.
- For high-risk work, separate research, implementation, and verification into distinct stages.

## Mandatory Output Sections

- Design brief
- System architecture
- Agent matrix
- Copilot customization bundle
- Runtime artifacts
- Verification and recovery plan
- Optimization strategy
- Rollout plan
