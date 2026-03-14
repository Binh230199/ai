---
name: cpp-static-analysis
description: >
  Use when asked to fix static analysis violations in C/C++ code — from
  clang-tidy, cppcheck, Coverity, MISRA C:2012, or AUTOSAR C++14 reports.
  Provides a safe per-rule fix workflow that prevents cascading new violations.
  Covers AUTOSAR C++14, MISRA C:2012, CERT C++, and clang-tidy findings.
  Does NOT cover tool setup or CI/CD configuration.
argument-hint: <rule-id|file|report>
---

# C/C++ Static Issue Fix Workflow

This skill guides **safe, rule-by-rule remediation** of static analysis findings
in automotive C/C++ codebases. It is designed to prevent the common failure mode
where fixing one rule introduces a violation of another.

---

## When to Use This Skill

- A task says "fix static issues", "clean up warnings", "fix MISRA violations", etc.
- IDE / `problems` panel shows clang-tidy or cppcheck warnings.
- User pastes a Coverity, PC-lint, or static analysis report.
- A commit diff contains `// NOLINT` or `// cppcheck-suppress` that needs review.
- Pre-commit: final scan before pushing code for review.

---

## Source of Issues

Three intake paths — all lead to the same fix workflow:

| Path | How to collect | Rule ID available? |
|---|---|---|
| **IDE / problems tool** | Use `problems` tool to list active diagnostics | Yes — clang-tidy check name or rule ID |
| **Self-review** | Use `changes` tool on staged diff; `codebase` search for patterns | Sometimes — derive from pattern |
| **Report text** | User pastes Coverity / PC-lint output | Yes — Coverity CID or rule ID |

---

## Fix Workflow — Follow in Order

### Step 1: Collect & Group Issues

Gather all issues from the available source. Group them by **Rule ID**:

```
AUTOSAR M5-0-2   → 4 occurrences in AudioManager.cpp
AUTOSAR A7-1-1   → 2 occurrences in SensorDriver.cpp
MISRA C 14.4     → 1 occurrence in can_driver.c
clang-tidy modernize-use-nullptr → 6 occurrences across 3 files
```

**Never mix rule IDs in a single fix pass.**

---

### Step 2: Prioritize

Fix in this order:
1. **Mandatory / Required** rules (MISRA Required, AUTOSAR Required) — safety-critical.
2. **Advisory** rules — quality improving.
3. **clang-tidy** modernization / style findings — lowest risk.

If the report comes from Coverity: fix **High** severity defects first.

---

### Step 3: Load the Rule Guide

For each Rule ID, load its guide from the `cpp-static-analysis/references/` subfolder:

| Rule ID pattern | Reference path |
|---|---|
| `AUTOSAR A*` or `AUTOSAR M*` | `cpp-static-analysis/references/autosar-cpp14/<RULE-ID>.md` |
| `MISRA C *` | `cpp-static-analysis/references/misra-cpp/<RULE-ID>.md` |
| `CERT C++ *` | `cpp-static-analysis/references/cert-cpp/<RULE-ID>.md` |
| clang-tidy check | `cpp-static-analysis/references/static/<check-name>.md` |

**If no guide file exists yet for this rule:**
1. Inform the user: _"No per-rule guide for `<ID>` yet. Add
   `cpp-static-analysis/references/<category>/<ID>.md` when this rule recurs."_
2. Fall back to `lang-cpp-code-writing` / `lang-c-code-writing` for general
   idiom guidance, but proceed conservatively — prefer the minimal transformation.
3. Always verify the fix does not trigger related rules (see Step 5).

---

### Step 4: Apply the Compliant Transformation

Use **only** the transformation pattern described in the rule guide.

**Rules for applying fixes:**

- Fix **one rule at a time** — complete all occurrences of Rule X before moving
  to Rule Y.
- Change **only the lines necessary** — do not reformat surrounding code.
- Do not change related code "while you're there" — separate commits.
- If a fix requires changes in more than one file, apply them in the same commit
  but document all affected files in the commit message.

---

### Step 5: Post-Fix Verification

After fixing all occurrences of a rule, verify with the **Post-Fix Checklist**
from the rule guide. If no guide exists, manually check:

1. Re-read the modified lines — does the fix match the "Compliant" example?
2. Check the **Related Rules** list in the guide. For each related rule,
   scan the modified lines for a new violation.
3. Compile mentally: are there new implicit conversions, narrowing, or type
   changes introduced?
4. If `problems` tool is available: re-run and confirm the finding is gone
   and no new findings appeared in the same file.

---

### Step 6: Suppression (Last Resort)

If a fix is technically impossible (e.g., hardware register access requires
`reinterpret_cast`, or a third-party API forces a narrowing conversion):

```cpp
// NOLINTNEXTLINE(cppcoreguidelines-pro-type-reinterpret-cast)
// Justification: Direct MMIO register access mandated by BSP spec §4.2.
// Deviation permit: PROJ-DEV-042 — approved by safety architect.
volatile uint32_t* reg = reinterpret_cast<volatile uint32_t*>(kBaseAddr);
```

**Rules for suppression:**
- Every `// NOLINT` or `// cppcheck-suppress` **must** have a justification comment.
- Bare `// NOLINT` with no reason is **not acceptable** — treat it as a new violation.
- Suppression of MISRA Mandatory rules requires a formal deviation permit reference.

---

### Step 7: Commit

One commit per Rule ID (or one commit per logical group of the same rule across files):

```
static(<scope>): fix AUTOSAR M5-0-2 narrowing conversion in AudioManager

Replaced implicit narrowing int→uint8_t with explicit static_cast.
Post-fix: verified no new A4-7-1 (overflow) violations introduced.
```

Commit type: `static` — see project commit convention.

---

## Quick Reference — Common Patterns Without a Guide

Use these only when no `cpp-static-analysis/references/` guide exists for the rule.

### Narrowing conversion (AUTOSAR M5-0-2 / MISRA 10.3)

```cpp
// ❌ Implicit narrowing
uint8_t val = some_int_expr;

// ✅ Explicit cast — add bounds assertion if value range is not proven
assert(some_int_expr >= 0 && some_int_expr <= 255); // or static_assert
uint8_t val = static_cast<uint8_t>(some_int_expr);
```

### Boolean context (MISRA C 14.4)

```cpp
// ❌ Non-boolean controlling expression
if (ptr) { ... }
if (count) { ... }

// ✅ Explicit comparison
if (ptr != nullptr) { ... }
if (count != 0U) { ... }
```

### constexpr (AUTOSAR A7-1-1)

```cpp
// ❌ const value known at compile time
const uint32_t kMaxRetries = 5U;

// ✅
constexpr uint32_t kMaxRetries = 5U;
```

### Explicit new/delete (AUTOSAR A18-5-2)

```cpp
// ❌
Sensor* s = new TemperatureSensor(id);
delete s;

// ✅
auto s = std::make_unique<TemperatureSensor>(id);
```

### nullptr over NULL / 0 (clang-tidy modernize-use-nullptr)

```cpp
// ❌
if (ptr == NULL) { ... }
callback_fn = 0;

// ✅
if (ptr == nullptr) { ... }
callback_fn = nullptr;
```

---

## Cross-Rule Contamination Map

The most common fix-triggers-new-violation patterns. Always check these after
applying the primary rule fix:

| Fix applied | Common new violation to check |
|---|---|
| Added `static_cast<T>` (M5-0-2) | A4-7-1 — arithmetic result within type range? |
| Added `static_cast<T>` | MISRA 10.5 — appropriate essential type cast? |
| Changed `const` to `constexpr` (A7-1-1) | Does expression remain valid in constexpr context? |
| Replaced `new` with `make_unique` (A18-5-2) | A8-4-7 — ownership transfer via parameter correct? |
| Added `!= nullptr` check (MISRA 14.4) | Redundant null check if pointer already validated upstream? |
| Replaced `NULL` with `nullptr` | Function overload resolution changed? |
| Removed `reinterpret_cast` | Does the replacement `static_cast` preserve MMIO semantics? |

---

## Prerequisites

- GCC 9+ or Clang 12+ toolchain installed.
- CMake 3.16+ on PATH.
- For cross-compilation: ARM/AArch64 sysroot or Android NDK r25+.
- `ninja` build tool recommended for faster builds.


## Step-by-Step Workflows

The step-by-step fix workflow is defined in the **Fix Workflow** section below.
Summary: collect violation report → fix one rule at a time → rebuild to confirm no regression → commit per rule.


## Troubleshooting

- **Fix introduced a new violation** — re-run the tool after each rule batch; revert and refine if new violations appear.
- **`clang-tidy` takes too long** — run on changed files only: `clang-tidy $(git diff --name-only HEAD | grep -E '\.(cpp|hpp|h)$')`.
- **False positive from a third-party header** — add the header path to `HeaderFilterRegex` in `.clang-tidy` to exclude it from reporting.
- **Suppression comment not working** — for clang-tidy use `// NOLINT(<check-name>)` at the end of the violating line; for cppcheck use `// cppcheck-suppress <id>`.


## References Folder Layout

```
cpp-static-analysis/references/
├── autosar-cpp14/     ← one .md per AUTOSAR rule (e.g., M5-0-2.md, A7-1-1.md)
├── misra-cpp/         ← one .md per MISRA rule (e.g., 14-4.md, 10-3.md)
├── cert-cpp/          ← one .md per CERT rule
└── static/            ← one .md per clang-tidy check or cppcheck category
```

Add a new rule guide whenever a rule is encountered for the first time.
Each rule guide file follows this template:

```markdown
# Rule: <ID> — <short title>

## Rule Statement
Exact wording from the standard (no paraphrasing).

## Trigger Patterns
Code patterns that cause a violation — with examples.

## Compliant Transformations
Exact transformation to apply — before/after code samples.

## What NOT To Do
Wrong "fixes" that still violate this rule or introduce a new one.

## Post-Fix Verification Checklist
- [ ] Check these related rules after applying the fix.

## Suppression (if unavoidable)
Correct suppression annotation with required justification format.
```
