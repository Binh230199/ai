---
name: "design-agentic-system"
description: "Design a complete GitHub Copilot-based agentic AI system from a user brief, including agents, skills, prompts, hooks, runtime artifacts, integrations, and rollout guidance."
argument-hint: "Describe the system goal, domain, constraints, integrations, and success criteria"
agent: "agentic-system-orchestrator"
---

Design a complete GitHub Copilot-based agentic AI system for the provided goal.

Use the `agentic-system-factory` skill, specialist subagents, and the bundled templates.

Your job is to:

1. extract or confirm the design brief
2. design the execution model and agent roles
3. map the design into a Copilot customization bundle
4. define runtime artifacts, verification gates, and recovery logic
5. produce a practical delivery package in English

If the request is missing critical information, identify the gaps explicitly before finalizing the design.
