---
name: agentic-system-factory
description: 'Design GitHub Copilot-based agentic AI systems. Use when turning a user brief into a complete system with agents, prompts, skills, instructions, hooks, MCP integration, manifests, runbooks, and rollout guidance.'
argument-hint: 'Describe the target system, domain, infrastructure, integrations, constraints, and success criteria'
user-invocable: true
---

# Agentic System Factory

Use this skill to design complete agentic AI systems on top of GitHub Copilot.

## What This Skill Produces

- a structured design brief
- a system architecture and execution model
- a role matrix for orchestrators and specialist agents
- a `.github/` customization bundle plan
- runtime artifacts such as manifests, ledgers, runbooks, and reports
- verification, recovery, and rollout guidance

## When To Use

- designing a new Copilot-based engineering automation system
- turning a workflow idea into prompts, agents, skills, hooks, and integrations
- creating systems for complex engineering, operational, documentation, or release workflows
- reviewing whether a proposed agentic system is actually completable and efficient

## Required Inputs

Gather or confirm the following whenever possible:

- business or engineering objective
- domain and target workflow
- repository or workspace scope
- build, test, and execution environment
- external systems or MCP servers
- approval, security, or policy constraints
- completion criteria and verification rules
- preferred output format or delivery package

## Procedure

1. Use the [requirements intake template](./assets/requirements-intake-template.md) to normalize the brief.
2. Use the [design procedure](./references/design-procedure.md) to shape the architecture.
3. Apply the [pattern catalog](./references/pattern-catalog.md) to choose robust execution patterns.
4. Map the architecture into a Copilot bundle using `references/copilot-bundle-template.md`.
5. Validate completeness with the [delivery contract](./references/delivery-contract.md).
6. Use the [worked example](./references/worked-example.md) when a concrete reference design will help.
7. Deliver the design in English with clear, reusable artifacts.

## Deliverables

- system brief
- architecture blueprint
- agent and tool matrix
- file bundle plan
- artifact and manifest plan
- hook and integration strategy
- optimization strategy
- implementation roadmap

## References

- [Design procedure](./references/design-procedure.md)
- [Pattern catalog](./references/pattern-catalog.md)
- [Delivery contract](./references/delivery-contract.md)
- [Worked example](./references/worked-example.md)

## Templates

- [Requirements intake template](./assets/requirements-intake-template.md)
- System blueprint template: `references/system-blueprint-template.md`
- Copilot bundle template: `references/copilot-bundle-template.md`
- Implementation roadmap template: `references/implementation-roadmap-template.md`

