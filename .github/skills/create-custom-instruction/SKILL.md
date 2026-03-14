---
name: create-custom-instruction
description: >
  Use when asked to create, update, or review a VS Code custom instruction file
  (.instructions.md or copilot-instructions.md). Provides the correct file format,
  frontmatter fields, location rules, and writing guidelines for effective instructions.
argument-hint: <instruction-name> [applyTo glob pattern]
---

# Create a Custom Instruction File

Custom instructions define coding standards, conventions, and guidelines that
Copilot applies automatically — either to all requests (always-on) or to specific
files matching a glob pattern (file-based).

## When to Use This Skill

- User asks to create a new `.instructions.md` file for a specific language, framework, or project area.
- User wants to add or update project-wide coding standards in `.github/copilot-instructions.md`.
- User wants instructions applied only to certain file types (e.g., `**/*.cpp`, `**/test/**`).

## File Locations

| Scope | Location |
|---|---|
| Project-wide (always-on) | `.github/copilot-instructions.md` |
| File-based (conditional) | `.github/instructions/<name>.instructions.md` |
| User profile (personal, all workspaces) | `~/.copilot/instructions/<name>.instructions.md` |

Directories are searched **recursively** — group by team/language/module is allowed:
```
.github/instructions/
  cpp/
    autosar.instructions.md
  android/
    kotlin.instructions.md
  testing/
    unit-tests.instructions.md
```

## File Format

### `.github/copilot-instructions.md` (always-on, no frontmatter)
```markdown
# Project Coding Standards

- Use C++17. No exceptions in embedded code.
- All public APIs must have Doxygen comments.
- Prefer `std::unique_ptr` over raw pointers.
```

### `.instructions.md` (file-based, with frontmatter)
```markdown
---
name: 'C++ Automotive Standards'
description: 'AUTOSAR and MISRA coding conventions for C++ source files'
applyTo: '**/*.{cpp,hpp,c,h}'
---

# C++ Coding Standards

- Use fixed-width integer types: `uint8_t`, `int32_t` — never `int` or `long`.
- Every pointer must be null-checked before dereferencing.
- No `dynamic_cast` in safety-critical paths (AUTOSAR A5-2-3).
```

## Frontmatter Fields

| Field | Required | Description |
|---|---|---|
| `name` | No | Display name in the UI. Defaults to file name. |
| `description` | No | Short description shown on hover. Used for semantic matching. |
| `applyTo` | No | Glob pattern for auto-apply. Without this, file is NOT applied automatically. |

## Step-by-Step Workflow

### Step 1: Determine scope
- **Project-wide rule** (all files) → `copilot-instructions.md`
- **Language/framework-specific rule** → `.instructions.md` with `applyTo`

### Step 2: Create the file in the correct location

### Step 3: Write the frontmatter (for `.instructions.md`)
- Set `applyTo` to the appropriate glob pattern.
- Write `description` concisely — it helps the AI decide when to apply.

### Step 4: Write the instruction body
Follow these guidelines:
- **One rule per bullet** — short, self-contained statements.
- **Include the "why"** when non-obvious: `"Use date-fns, not moment.js — moment is deprecated and increases bundle size."`
- **Show code examples** for allowed and forbidden patterns.
- **Skip what linters already enforce** — focus on non-obvious conventions.
- **Reference related files** using Markdown links rather than duplicating rules.

## Instruction Quality Checklist

- [ ] Each rule is a single, actionable statement.
- [ ] `applyTo` pattern is correct and minimal (not `**` if it should only apply to C++ files).
- [ ] Non-obvious rules include rationale.
- [ ] Code examples included for complex rules.
- [ ] No duplication with existing `copilot-instructions.md`.

## Examples

### Language-specific
```markdown
---
name: 'Kotlin Android Standards'
description: 'Kotlin conventions for Android Automotive app code'
applyTo: '**/*.kt'
---
- Use `StateFlow` instead of `LiveData` for new code.
- Inject dependencies via Hilt — do not use `ServiceLocator`.
- Every `suspend` function must be called from a coroutine scope, never from `GlobalScope`.
```

### Test file rules
```markdown
---
name: 'Unit Test Standards'
description: 'Conventions for unit test files'
applyTo: '**/{test,tests}/**/*.{cpp,kt,java}'
---
- Test function name format: `GIVEN_<state>_WHEN_<action>_THEN_<expected>`.
- Do not use real filesystem or network in unit tests — mock all I/O.
- Each test must have exactly one logical assertion.
```

## Prerequisites

- VS Code 1.87+ with the GitHub Copilot extension installed.
- A workspace with a `.github/` directory at the root.
- Familiarity with glob patterns for the `applyTo` field.


## Troubleshooting

- **AI never auto-loads the skill / agent / instruction** — verify `disable-model-invocation` is not `true` and `description` contains a clear "Use when ..." trigger phrase.
- **Skill / prompt not shown in the `/` command menu** — check that `user-invocable` is not `false` and the file is saved to the correct `.github/` subdirectory.
- **`name` validator error (`FM_NAME_DIR_MISMATCH`)** — the `name` frontmatter field must exactly match the directory/file name (case-sensitive, lowercase, hyphens only).
- **Companion file not found by the AI** — reference files with paths relative to the skill/instruction/prompt file (e.g., `./examples/good.cpp`).


## References
- [VS Code Custom Instructions Docs](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)
