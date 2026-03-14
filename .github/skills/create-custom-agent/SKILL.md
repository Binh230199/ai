---
name: create-custom-agent
description: >
  Use when asked to create, update, or review a VS Code custom agent (.agent.md).
  Provides the correct file format, frontmatter fields, tool configuration, handoff
  patterns, and guidelines for designing effective, focused agents.
argument-hint: <agent-name> [role description]
---

# Create a Custom Agent

Custom agents define a **persistent persona** with specific tool restrictions,
model preferences, and optional handoff workflows. Use them when you need the AI
to adopt a specialized role (e.g., security reviewer, architect, planner) with
consistent behavior across all conversations.

## When to Use an Agent (vs other customizations)

| Need | Use |
|---|---|
| Persistent role with tool restrictions | **Custom Agent** (`.agent.md`) |
| Single-task slash command | Prompt file (`.prompt.md`) |
| Reusable domain knowledge/procedures | Skill (`SKILL.md`) |
| Coding standards applied automatically | Instructions (`.instructions.md`) |

## File Location

| Scope | Location |
|---|---|
| Workspace (shared with team) | `.github/agents/<agent-name>.agent.md` |
| User profile (personal, all workspaces) | `~/.copilot/agents/<agent-name>.agent.md` |

> VS Code also detects any `.md` file in `.github/agents/`.

## File Format

```markdown
---
name: <agent-name>
description: <Short description shown as placeholder text in chat input>
argument-hint: <hint shown in chat input field>
tools:
  - <tool-name>
  - <tool-name>
model: <model-name>           # optional; defaults to user-selected model
user-invocable: true          # show in agents dropdown (default: true)
disable-model-invocation: false  # allow use as subagent (default: false)
handoffs:
  - label: <Button Label>
    agent: <target-agent-name>
    prompt: <pre-filled prompt for next agent>
    send: false               # true = auto-submit prompt
---

# Agent Instructions

Detailed instructions for the agent's behavior, persona, and workflow.
Reference instructions files and skills with Markdown links.

## Role
...

## Workflow
...

## Output Format
...
```

## Frontmatter Fields

| Field | Required | Description |
|---|---|---|
| `name` | No | Display name. Defaults to file name. |
| `description` | No | Shown as placeholder in chat input. Describes the role. |
| `argument-hint` | No | Hint text for user input guidance. |
| `tools` | No | Allowed tools. Omit = only default tools. Empty `[]` = no tools. |
| `agents` | No | Allowed subagents. `*` = all agents, `[]` = no subagents. |
| `model` | No | Specific model or priority list `[model-a, model-b]`. |
| `user-invocable` | No | `false` = hide from dropdown, still usable as subagent. |
| `disable-model-invocation` | No | `true` = cannot be invoked as subagent. |
| `handoffs` | No | Transition buttons with target agent, label, prompt. |

## Available Built-in Tools

Common tools to specify in `tools:` field:

| Tool name | Description |
|---|---|
| `read_file` | Read file contents |
| `list_dir` | List directory contents |
| `grep_search` | Search in files |
| `semantic_search` | Semantic code search |
| `file_search` | Find files by pattern |
| `create_file` | Create new files |
| `replace_string_in_file` | Edit existing files |
| `run_in_terminal` | Execute shell commands |
| `fetch_webpage` | Fetch URL content |
| `get_errors` | Get compile/lint errors |
| `github_repo` | GitHub repository operations |

## Agent Design Principles

### Tool Restriction by Role
- **Read-only agents** (architect, planner, reviewer): `[read_file, list_dir, grep_search, semantic_search, fetch_webpage]`
- **Implementation agents**: add `create_file`, `replace_string_in_file`
- **DevOps / automation agents**: add `run_in_terminal`
- **Review agents**: no terminal, no file write — read-only only.

### Principle of Least Privilege
Grant only tools the agent genuinely needs. A planning agent that can run
terminal commands is a liability.

## Handoff Patterns

Design handoffs for multi-step workflows:

```markdown
handoffs:
  - label: Start Implementation
    agent: implementation
    prompt: |
      Implement the plan described above. Follow the architecture decisions made.
    send: false
  - label: Request Review
    agent: reviewer-feature
    prompt: Review the implementation above for correctness and security.
    send: true
```

## Step-by-Step Workflow

### Step 1: Define the role
Answer: What persona does this agent adopt? What is it NOT allowed to do?

### Step 2: Choose tools
Start with the minimum. Add only what the role genuinely needs.

### Step 3: Create the file
```
.github/agents/<agent-name>.agent.md
```

### Step 4: Write the body
- Define the **role** clearly in 1-2 sentences.
- Write the **workflow** as ordered steps.
- Specify the **output format** expected.
- Reference related instructions using Markdown links.

### Step 5: Add handoffs (if part of a workflow)

### Step 6: Verify
- [ ] Tools list follows least-privilege principle.
- [ ] `description` is clear enough for the user to understand when to pick this agent.
- [ ] Read-only agents have no write or terminal tools.
- [ ] Handoff target agents exist.

## Examples

### Planning Agent (read-only)
```markdown
---
name: planner
description: Analyzes requirements and generates a detailed implementation plan. Does not write code.
tools:
  - read_file
  - list_dir
  - grep_search
  - semantic_search
  - fetch_webpage
handoffs:
  - label: Start Implementation
    agent: implementation
    prompt: Implement the plan above.
    send: false
---

# Planner Agent

You are a senior software architect. Your job is to analyze the codebase and
requirements, then produce a detailed implementation plan.

## Workflow
1. Read relevant source files and understand current architecture.
2. Identify affected components.
3. Propose a step-by-step implementation plan with clear decisions.
4. Do NOT write code.

## Output Format
- Architecture decision summary
- Ordered implementation steps with file paths
- Risk/dependency notes
```

### Security Reviewer Agent
```markdown
---
name: reviewer-security
description: Reviews code for security vulnerabilities. No code modifications.
tools:
  - read_file
  - grep_search
  - semantic_search
  - get_errors
---

# Security Review Agent

Review the provided code for OWASP Top 10 vulnerabilities, unsafe memory
operations, and automotive cybersecurity concerns (ISO 21434).

## Output
End response with `[PASS]` or `[FAIL]` followed by numbered findings.
```

## Prerequisites

- VS Code 1.87+ with the GitHub Copilot extension installed.
- A workspace with a `.github/agents/` directory (create it if absent).
- Basic understanding of Markdown and YAML frontmatter syntax.


## Troubleshooting

- **AI never auto-loads the skill / agent / instruction** — verify `disable-model-invocation` is not `true` and `description` contains a clear "Use when ..." trigger phrase.
- **Skill / prompt not shown in the `/` command menu** — check that `user-invocable` is not `false` and the file is saved to the correct `.github/` subdirectory.
- **`name` validator error (`FM_NAME_DIR_MISMATCH`)** — the `name` frontmatter field must exactly match the directory/file name (case-sensitive, lowercase, hyphens only).
- **Companion file not found by the AI** — reference files with paths relative to the skill/instruction/prompt file (e.g., `./examples/good.cpp`).


## References
- [VS Code Custom Agents Docs](https://code.visualstudio.com/docs/copilot/customization/custom-agents)
- [Awesome Copilot Agents](https://github.com/github/awesome-copilot/tree/main/agents)
