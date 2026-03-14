---
name: create-custom-skill
description: >
  Use when asked to create, update, or review a VS Code Agent Skill (SKILL.md).
  Provides the correct directory structure, frontmatter fields, body format,
  and guidelines for writing effective, maintainable skills.
argument-hint: <skill-name> [brief description of capability]
---

# Create a Custom Agent Skill

Agent Skills are folders of instructions, scripts, and resources that Copilot
loads **on-demand** when relevant to a task. Unlike instructions (always-on),
skills are loaded only when the AI decides they are needed — keeping context efficient.

## When to Use This Skill

- User asks to create a new skill for a domain-specific capability or workflow.
- User wants to package reusable procedures (e.g., how to build, how to debug, how to write tests).
- User wants a capability that is portable across VS Code, Copilot CLI, and coding agents.

## When NOT to Create a New Skill

Create a new skill only when:
- The topic requires **step-by-step workflow** guidance beyond a simple rule.
- It needs **companion files** (scripts, templates, examples).
- It is triggered in a **different context** than existing skills.

Otherwise, **extend an existing skill** — avoid skill explosion.

## Prerequisites

- VS Code with GitHub Copilot extension installed.
- A `.github/skills/` directory at the workspace root (create it if absent).
- Basic understanding of YAML frontmatter syntax.
- Python 3.8+ (optional — only needed to run the `validate_skills.py` audit script).

## Directory Structure

```
.github/skills/
└── <skill-name>/               ← directory name MUST match `name` field in frontmatter
    ├── SKILL.md                ← required
    ├── examples/               ← optional: code examples
    │   ├── good-example.cpp
    │   └── bad-example.cpp
    └── scripts/                ← optional: helper scripts
        └── check.sh
```

> **Rule**: The directory name must exactly match the `name` field in frontmatter.

## SKILL.md File Format

```markdown
---
name: <skill-name>
description: >
  Use when [trigger condition]. Provides [what it helps with].
  [One more sentence about scope/domain if needed.]
argument-hint: <arg-hint shown in chat input>
user-invocable: true          # show as /slash-command (default: true)
disable-model-invocation: false  # allow automatic loading by AI (default: false)
---

# Skill Title

One-paragraph summary of what this skill does and its domain.

## When to Use This Skill

- Bullet list of trigger conditions (when should the AI load this skill).

## Prerequisites

- What context, tools, or knowledge is assumed.
- Required tools, SDKs, or environment setup.

## Step-by-Step Workflows

### Step 1: [Action]
...

### Step 2: [Action]
...

## Examples

### Good Pattern
```[language]
// compliant example
```

### Bad Pattern
```[language]
// non-compliant example — explanation of what is wrong
```

## Troubleshooting

- **Issue: [common problem]** — [solution]
- Common issues and how to resolve them.

## References

- Links to relevant documentation.
```

## Frontmatter Fields

| Field | Required | Description |
|---|---|---|
| `name` | **Yes** | Unique identifier. Lowercase, hyphens only. Max 64 chars. Must match directory name. |
| `description` | **Yes** | When to load and what it does. Max 1024 chars. This is the AI's trigger signal. |
| `argument-hint` | No | Hint shown in chat input field when invoked as `/skill-name`. |
| `user-invocable` | No | `false` = hide from `/` menu, AI can still auto-load. Default: `true`. |
| `disable-model-invocation` | No | `true` = only run on `/explicit-call`, AI never auto-loads. Default: `false`. |

## Skill Granularity Guidelines

**DO NOT** create one skill per rule/pattern. Instead, **cluster by domain and task type**:

| Too granular (bad) | Right granularity (good) |
|---|---|
| `cpp-nullptr-check` | `cpp-automotive` — all C++ patterns for embedded/automotive |
| `cmake-add-library` | `modern-cmake` — all CMake patterns |
| `junit-assertion-style` | `android-testing` — all Android test patterns |

**One skill = one senior engineer's mental checklist for one type of task.**

## Step-by-Step Workflow

### Step 1: Define the scope
Identify the domain and task type. Write the `description` first — if it's hard
to write a clear trigger condition, the skill boundary is wrong.

### Step 2: Create the directory
```
.github/skills/<skill-name>/
```
The directory name must be lowercase with hyphens and match the `name` frontmatter field exactly.

### Step 3: Create SKILL.md using the template above
Include all recommended sections: `## When to Use This Skill`, `## Prerequisites`,
`## Step-by-Step Workflows`, `## Troubleshooting`, `## References`.

### Step 4: Add companion files (optional)
- `examples/` — concrete good/bad code samples referenced from the body.
- `scripts/` — helper scripts the AI can execute.
- Reference them in SKILL.md with relative paths: `[good example](./examples/good.cpp)`

### Step 5: Verify
- [ ] Directory name matches `name` frontmatter field.
- [ ] `description` clearly states WHEN to use (the AI's trigger condition).
- [ ] Body contains all recommended sections (run `validate_skills.py` to check).
- [ ] Relative paths to companion files are correct.

## Examples of Good Description Fields

```yaml
# Good — clear trigger + what it does
description: >
  Use when writing or reviewing C++ code in an automotive embedded context.
  Covers null safety, RAII, fixed-width types, smart pointers, and error handling
  patterns compliant with AUTOSAR/MISRA in C++17.

# Bad — too generic
description: Help with C++ code.

# Bad — too narrow (should be merged into a broader skill)
description: Use when a pointer might be null.
```

---

## Validating All Skills

Use the bundled Python script to audit every SKILL.md for format compliance:

```bash
# From the workspace root (d:\AI)
python .github/skills/create-custom-skill/scripts/validate_skills.py

# Show file paths for all skills with issues
python .github/skills/create-custom-skill/scripts/validate_skills.py --fix-hints

# Errors only (suppress warnings)
python .github/skills/create-custom-skill/scripts/validate_skills.py --errors-only

# Machine-readable output
python .github/skills/create-custom-skill/scripts/validate_skills.py --json
```

The script checks every skill directory under `.github/skills/` and reports:

| Check | Severity | Description |
|---|---|---|
| `SKILL.md` exists | Error | Every skill directory must contain `SKILL.md` |
| `name` present in frontmatter | Error | Required frontmatter field |
| `description` present | Error | Required frontmatter field |
| `name` is lowercase-hyphens only | Error | Max 64 chars, must match directory name |
| Directory name matches `name` | Error | Prevents load failures |
| `description` starts with "Use when" | Warning | Needed for AI auto-loading |
| H1 title present | Error | Skill must have a `# Title` heading |
| `## When to Use This Skill` present | Error | Required section |
| `## Prerequisites` present | Warning | Strongly recommended |
| `## Step-by-Step Workflows` present | Warning | Strongly recommended |
| `## Troubleshooting` present | Warning | Strongly recommended |
| `## References` present | Warning | Strongly recommended |

**All warnings are fixable** — add the missing section with at least a brief explanation
or a `N/A` note if genuinely not applicable. Warnings accumulate quickly across 40+ skills;
address them after every new skill is created.

**Run this script after creating or updating any skill** to catch structural
regressions before they accumulate.

## Troubleshooting

- **AI never auto-loads the skill** — check that `description` contains a clear "Use when ..." trigger phrase and `disable-model-invocation` is not `true`.
- **Skill not shown in `/` menu** — verify `user-invocable` is not set to `false`.
- **Validator reports `FM_NAME_DIR_MISMATCH`** — the `name` frontmatter field must exactly match the folder name (case-sensitive lowercase).
- **Validator reports `BODY_NO_H1`** — add a `# Title` as the first line after the frontmatter.
- **False positive heading detected inside code block** — the validator strips fenced blocks before checking; ensure your fences use triple backticks (` ``` `).

## References
- [VS Code Agent Skills Docs](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- [AgentSkills Open Standard](https://agentskills.io/)
- [Awesome Copilot Skills](https://github.com/github/awesome-copilot/tree/main/skills)
