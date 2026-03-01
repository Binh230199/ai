# GitHub Copilot — Project-Wide Instructions

These instructions apply to every Copilot interaction in this workspace, regardless of file type or agent.

---

## Commit Convention (Conventional Commits)

All commit messages must follow this format:
```
<type>(<scope>): <short description>

[optional body]

[optional footer: TICKET-ID]
```

**Allowed types:**
| Type | Usage |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix (reference Jira ticket) |
| `test` | Adding or updating tests only |
| `static` | Fixing static analysis violations (mention rule ID) |
| `refactor` | Code restructuring without behavior change |
| `docs` | Documentation only |
| `format` | Whitespace, formatting, no logic change |
| `chore` | Build scripts, CI, dependencies |
| `perf` | Performance improvement |

**Examples:**
```
fix(bluetooth): null pointer dereference in connect() - RRRSE-3050
feat(sensor): add temperature calibration offset support - RRRSE-4100
static(network): fix AUTOSAR M5-0-2 narrowing conversion in TcpSocket
test(audio): add unit tests for volume clamping edge cases
```

---

## Agent Routing (used by ai_git_push script)

| Commit type | Reviewer agent |
|---|---|
| `fix` / `fixbug` | `reviewer-bugfix` |
| `feat` / `feature` | `reviewer-feature` |
| `static` | `reviewer-static` |
| `test` / `docs` / `format` / `chore` / `refactor` | `reviewer-light` |

---

## Output Protocol (for all reviewer agents)

All reviewer agents must end their response with exactly one of:
- `[PASS]` — no significant issues found
- `[FAIL]` — issues found (followed by numbered list)

This protocol is machine-parsed by the `ai_git_push` script.

---

## General Principles

- **Shift-Left**: Catch issues as early as possible — local review before push eliminates expensive server-side iteration
- **Scope discipline**: Each commit does exactly one thing. Mixed-concern commits must be split
- **Traceability**: Bug fix commits must reference a Jira ticket ID in the footer
- **No broken windows**: Do not add new TODOs, commented-out code, or magic numbers

---

## Language-Specific Rules

See path-scoped instruction files:
- C / C++: `.github/instructions/c-cpp.instructions.md` (auto-applied to `*.{c,cpp,h,hpp}`)

---

## Skills Available

| Skill | Path | Purpose |
|---|---|---|
| C/C++ Language Context | `.github/skills/lang-c-cpp/SKILL.md` | Patterns, anti-patterns, Doxygen templates |
| AUTOSAR M5-0-2 | `.github/skills/static-rules/autosar-m5-0-2/SKILL.md` | Narrowing conversion fix guide |
| MISRA C Rule 14.4 | `.github/skills/static-rules/misra-c-rule-14-4/SKILL.md` | Boolean context fix guide |
