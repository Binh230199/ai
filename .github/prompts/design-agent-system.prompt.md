---
name: design-agent-system
description: >
  Design a complete AI agent system from a role description. Creates the
  .agent.md, all SKILL.md files, all .instructions.md files, and all
  .prompt.md files — wired together and production-ready in one shot.
argument-hint: <role, e.g. "planner", "security reviewer", "data analyst">
agent: Agent System Architect
tools:
  - create_file
  - replace_string_in_file
  - read_file
  - codebase
  - search
---

Design a complete agent system for the role: **${input:role:e.g. planner, security reviewer, refactoring assistant}**

## What the Agent System Architect must do

Work through all six phases without stopping:

### Phase 0 — Load Skills
Load all four creation skills before writing any file:
`create-custom-agent`, `create-custom-skill`, `create-custom-instruction`, `create-custom-prompt`.

### Phase 1 — Plan
Analyze the role. Print a design plan table listing every file to be created
(agent, skills, instructions, prompts) with their purpose. Do not create files yet.

### Phase 2 — Create Agent File
Create `.github/agents/<name>.agent.md` with complete frontmatter and all
required body sections: persona, loaded skills, workflow, output format, quality rules.

### Phase 3 — Create Skills
For each skill in the plan, create `.github/skills/<name>/SKILL.md` with all
required sections: When to Use, Prerequisites, Step-by-Step Workflow,
Examples, Troubleshooting. Every step must be concrete and actionable.

### Phase 4 — Create Instructions
For each instruction in the plan, create `.github/instructions/<name>.instructions.md`
with valid `applyTo` glob and specific, verifiable rules (no vague statements).

### Phase 5 — Create Prompts
For each prompt in the plan, create `.github/prompts/<name>.prompt.md` with
`agent: <Agent Name>` in frontmatter, `${input:...}` variables for parameters,
and a clear task body.

### Phase 6 — Summary
Output the complete file inventory, usage guide, and end with `[SCAFFOLD_COMPLETE]`.

## Quality Requirements

- No `<placeholder>`, `TODO`, or `...` in any created file.
- Every skill `name` in frontmatter must exactly match its directory name.
- Every prompt must reference the agent created in Phase 2.
- The agent body must list every created skill by name and file path.
- All YAML frontmatter must be valid (quoted strings with colons, correct indentation).
