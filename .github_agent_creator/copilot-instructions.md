# Agentic System Factory

This workspace is used to design GitHub Copilot-based agentic systems.

## Operating Model

- Treat each request as system design work, not as a loose brainstorming session.
- Convert the user's brief into explicit objective, scope, inputs, constraints, exit criteria, and deliverables before designing the system.
- Prefer specialist subagents for requirements analysis, workflow architecture, Copilot bundle mapping, integration design, and quality review.
- Keep durable design state in files and artifacts instead of relying on long chat history.
- Write all design outputs in English unless the user explicitly asks for another language.

## Required Deliverables

A complete agentic-system design should normally include:

- system objective and scope
- execution model and phase flow
- agent role matrix
- tool and permission strategy
- instruction, prompt, agent, skill, hook, and MCP bundle map
- runtime artifacts and manifests
- verification and completion gates
- recovery and resume strategy
- token and latency optimization plan
- rollout and validation plan

## Completion Rules

- Do not call a design complete if it lacks exit criteria.
- Do not call a design complete if it lacks verification gates.
- Do not call a design complete if it lacks a recovery or resume approach.
- Do not collapse everything into one agent; use narrow roles with clear boundaries.

## Copilot Customization Rules

- Keep one concern per customization file whenever practical.
- Every skill, agent, prompt, and instruction must have a keyword-rich description.
- Custom agents must have minimal tool sets and explicit boundaries.
- Skills should package repeatable workflows, templates, and references.
- Hooks must stay fast, deterministic, and auditable.
- Avoid broad always-on instructions unless they truly apply to every task.

## Review Standards

- Prefer manifest-driven workflows over vague task lists.
- Prefer research-before-write for risky or ambiguous tasks.
- Prefer verifier agents or deterministic hooks over self-certification.
- Prefer structured outputs that another agent can consume without re-reading a long narrative.
