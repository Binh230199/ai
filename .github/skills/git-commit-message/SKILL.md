---
name: git-commit-message
description: >
  Use when asked to generate a git commit message for a code change.
  Reads the diff (unstaged or staged), infers the commit type and scope
  from the changed files, then produces a commit message that matches the
  project's convention — either from a templates/commit-template.md file
  in this skill folder, or derived from the last 5–10 commits in the repo.
argument-hint: [staged|unstaged|<commit-hash>]
---

# Git Commit Message Generator

Produces a well-formed commit message for any code change, matching the
project's existing convention without requiring the author to remember format rules.

---

## When to Use This Skill

- User says "generate commit message", "write commit", "create commit", etc.
- After finishing a coding task — produce a ready-to-use commit message.
- User pastes a diff and asks how to commit it.

---

## Step-by-Step Workflows

The commit message generation workflow is defined in the numbered Step sections below
(Step 1 – Step 6). Follow them in order: read diff → infer type/scope → check for Jira
ticket → compose subject → write body → output the final message.

### Step 1: Collect the Diff

Determine the state of changes and collect the diff content:

| Situation | Command to run |
|---|---|
| Changes **not yet staged** | `git diff > diff.diff` then read the file |
| Changes **already staged** | `git diff --staged > diff.diff` then read the file |
| Reviewing a past commit | `git show <hash> --stat` |
| Agent has `changes` tool | Use `changes` tool directly — no need for git commands |

If the workspace has both staged and unstaged changes, ask the user which set
to commit, or check `git status` output first.

---

### Step 2: Determine the Commit Convention

#### 2A — Check for template file

Look for `templates/commit-template.md` inside this skill folder
(`d:\AI\.github\skills\git-commit-message\templates\commit-template.md`).

If the file exists, load it and use its format exactly.

#### 2B — Derive from recent history (fallback)

If no template file exists, run:

```bash
git log --oneline -10
```

Analyze the last 10 commits to extract:
- **Prefix style**: `type(scope):`, `[TYPE]`, `feat:`, `fix/`, bare sentence, etc.
- **Scope conventions**: module names, file paths, component identifiers used.
- **Tense**: imperative ("add", "fix") vs. past tense ("added", "fixed").
- **Length**: subject line character limit observed.
- **Body / footer presence**: is a body used? Is a ticket ID pattern present?

Replicate the detected format exactly — pick the majority pattern if there is
variation.

---

### Step 3: Analyze the Diff

Read the diff and extract:

1. **What changed** — summarize in one phrase (e.g., "null check in connect()")
2. **Why** (if inferable from context, surrounding code, or variable/function names)
3. **Affected files and modules** — determine the scope from file paths:

| Path pattern | Scope example |
|---|---|
| `src/audio/`, `audio/` | `audio` |
| `src/bluetooth/BluetoothManager.*` | `bluetooth` |
| `include/sensor/`, `sensor/` | `sensor` |
| `CMakeLists.txt`, `Android.bp` | `build` |
| `test/`, `*_test.*`, `*Test.*` | `test` |
| `docs/`, `*.md` | `docs` |
| `res/layout/`, `*.xml` (Android) | `ui` |
| `res/values/strings.xml` | `i18n` |

If changes span multiple unrelated modules, consider splitting into separate commits.
Flag it: _"This diff touches X and Y — recommend two commits."_

4. **Commit type** — pick from the project convention (see template or history).
   When using Conventional Commits:

| Type | When to use |
|---|---|
| `feat` | New functionality added |
| `fix` | Bug fix |
| `test` | Adding or updating tests only |
| `static` | Fixing static analysis violations |
| `refactor` | Code restructured, no behavior change |
| `docs` | Documentation only |
| `format` | Whitespace / formatting, zero logic change |
| `chore` | Build scripts, CI, dependencies |
| `perf` | Performance improvement |

---

### Step 4: Compose the Commit Message

Apply the format from Step 2 with the content from Step 3.

#### Standard output (Conventional Commits + body)

```
<type>(<scope>): <short imperative description>

<optional body — what changed and why, wrapped at 72 chars>
<reference to related work if present in existing history>

<optional footer: TICKET-ID>
```

**Subject line rules:**
- Max 72 characters.
- Lowercase after the colon.
- Imperative mood: "add", "fix", "remove" — not "added", "fixes", "removed".
- No period at the end.

**Body rules (include when):**
- The change is non-trivial and the subject alone is not self-explanatory.
- The "why" is not obvious from the diff.
- A follow-up action is needed (e.g., "requires migration step").

**Footer rules:**
- Include Jira ticket if present in recent commit history pattern.
- Format: `TICKET-ID` on its own line, or `Fixes: TICKET-ID`.

---

### Step 5: Output

Present the commit message in a code block ready to copy:

```
feat(bluetooth): add null guard in connect() before socket creation

connect() crashed when called before the adapter was initialized.
Added an early-return guard with an error log to handle the uninitialized state.

RRRSE-3050
```

Then offer:
- If the diff touches multiple concerns: suggest how to split into separate commits.
- If the type is ambiguous: briefly explain the choice.
- If no ticket ID pattern is found in history: omit the footer silently.

---

### Step 6: Apply (optional)

If the user confirms the message, run:

```bash
git commit -m "<subject>" -m "<body>"
```

Or for a multi-line message, write it to a temp file:

```bash
git commit -F /tmp/commit_msg.txt
```

---

## Prerequisites

- `git` installed and a repository initialized.
- Project following a commit convention (e.g. Conventional Commits).
- Staged or unstaged changes ready to commit (`git diff --cached` or `git diff`).

## Troubleshooting

- **Unsure of the commit type** — check the last 10 commits with `git log --oneline -10`; match the convention already in use.
- **Scope is unclear** — use the top-level module, package, or component name; omit scope for cross-cutting changes.
- **`fix` vs `refactor`** — if behavior changes (even just a bug fix), use `fix`; if only structure changes with no behavior change, use `refactor`.
- **Commit subject is too long** — keep the subject line ≤ 72 characters; push extra detail into the body.


## References

- [Conventional Commits specification](https://www.conventionalcommits.org/)
- [Git `commit` documentation](https://git-scm.com/docs/git-commit)
- Project commit template: [`templates/commit-template.md`](./templates/commit-template.md)
