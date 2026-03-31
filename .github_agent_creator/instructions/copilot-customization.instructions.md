---
description: "Use when creating or updating GitHub Copilot customizations such as instructions, prompts, agents, hooks, or skills. Covers frontmatter, discovery, tool scoping, and packaging quality."
applyTo: ".github/**/*.md, .github/**/*.json, .github/hooks/scripts/**/*.mjs"
---

# Copilot Customization Design Rules

- Keep descriptions specific and discovery-friendly. Start them with "Use when..." whenever practical.
- Quote YAML description values that contain punctuation.
- Keep custom agents narrow. Each agent should own one role and one kind of output.
- Do not give execution tools to research-only agents.
- Do not put multi-stage workflows into prompt files when a skill or orchestrator agent is the better fit.
- Use skills for repeatable procedures, references, and templates.
- Use hooks for deterministic enforcement, not for vague guidance.
- Keep `copilot-instructions.md` concise and universal.
- Avoid `applyTo: "**"` unless the instruction truly applies to nearly every coding task.
- Ensure the final bundle is coherent: prompt entrypoint, skill procedure, agent roles, and hook policies must agree.

## Frontmatter Expectations

- `*.agent.md`: require `description`; strongly prefer `name`, `tools`, and narrow responsibilities.
- `*.instructions.md`: require `description`; use `applyTo` only when the scope is file-based.
- `*.prompt.md`: strongly prefer `description`, `agent`, and `argument-hint`.
- `SKILL.md`: require `name` and `description`; the `name` must match the folder name.
