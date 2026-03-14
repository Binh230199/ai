# Commit Message Template

## Format

```
<type>(<scope>): <short description>

[optional body]

[optional footer: TICKET-ID]
```

## Allowed Types

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

## Examples

```
fix(bluetooth): null pointer dereference in connect() - PRJ-3050
feat(sensor): add temperature calibration offset support - PRJ-4100
static(network): fix AUTOSAR M5-0-2 narrowing conversion in TcpSocket
test(audio): add unit tests for volume clamping edge cases
```

## Rules

- Subject line: max 72 characters, imperative mood, no period at end.
- Body: wrap at 72 characters. Explain *what* and *why*, not *how*.
- Footer: Jira ticket ID on its own line (e.g. `PRJ-1234`).
- Every `fix` commit must reference a Jira ticket ID.
- Every `static` commit should mention the rule ID being fixed.
