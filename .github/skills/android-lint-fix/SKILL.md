---
name: android-lint-fix
description: >
  Use when asked to fix Android Lint, Kotlin compiler warnings, or Detekt
  violations in Kotlin/Java Android app code. Provides a safe per-rule fix
  workflow that prevents cascading new issues. Covers Android Lint IDs,
  Kotlin compiler warnings, and Detekt rules. Does NOT cover Lint tool
  setup or Gradle configuration.
argument-hint: <lint-id|file|report>
---

# Android Lint & Kotlin Static Issue Fix Workflow

This skill guides **safe, rule-by-rule remediation** of static analysis findings
in Android Kotlin/Java codebases. It is designed to prevent the common failure
mode where fixing one warning introduces another.

---

## When to Use This Skill

- A task says "fix lint issues", "clean up warnings", "fix Detekt violations".
- Android Studio / `problems` panel shows Lint or Kotlin compiler warnings.
- User pastes a Lint HTML/XML/text report.
- CI pipeline fails on a `./gradlew lint` step.
- Pre-commit: final cleanup before pushing for review.

---

## Source of Issues

Three intake paths — all lead to the same fix workflow:

| Path | How to collect | Rule ID available? |
|---|---|---|
| **IDE / problems tool** | Use `problems` tool to list active diagnostics | Yes — Lint issue ID |
| **Self-review** | Use `changes` tool on staged diff | Sometimes — derive from pattern |
| **Report file** | User pastes lint-results.xml or HTML report | Yes — Lint issue ID |

Parse each finding for exactly two fields: **Issue ID** (e.g., `HardcodedText`)
and **file + line** (e.g., `res/layout/activity_main.xml:12`).

---

## Fix Workflow — Follow in Order

### Step 1: Collect & Group Issues

Group all issues by **Lint Issue ID**:

```
HardcodedText        → 3 occurrences in res/layout/
NotifyDataSetChanged → 2 occurrences in adapters/
WrongConstant        → 1 occurrence in BluetoothService.kt
UnusedResources      → 4 occurrences
```

**Never mix Issue IDs in a single fix pass.**

---

### Step 2: Prioritize

Fix in this order:
1. **Error** severity (red in Android Studio) — may block build or cause crashes.
2. **Warning** severity — correctness or performance issues.
3. **Information** severity — style and best-practice suggestions.

Within each severity level, fix **security-related** issues first
(e.g., `HardcodedDebugMode`, `ExportedReceiver`, `SetJavaScriptEnabled`).

---

### Step 3: Load the Rule Guide

For each Issue ID, load its guide from the `references/` subfolder:

| Issue ID pattern | Reference path |
|---|---|
| Android Lint ID | `references/lint/<ISSUE-ID>.md` |
| Kotlin compiler warning | `references/kotlin/<WARNING-KEY>.md` |
| Detekt rule | `references/detekt/<RULE-ID>.md` |

**If no guide file exists yet for this rule:**
1. Inform the user: _"No per-rule guide for `<ID>` yet. Add
   `references/<category>/<ID>.md` when this rule recurs."_
2. Fall back to `lang-kotlin-code-writing` or `lang-java-code-writing` for
   general idiom guidance, but apply only the minimal transformation.
3. Always verify the fix does not trigger related rules (see Step 5).

---

### Step 4: Apply the Compliant Transformation

Use **only** the transformation pattern described in the rule guide.

**Rules for applying fixes:**

- Fix **one Issue ID at a time** — complete all occurrences before moving to
  the next ID.
- Change **only the lines necessary** — do not reformat surrounding code.
- Do not make "while you're here" improvements — separate commits.
- Resource file changes (XML layouts, strings) and Kotlin/Java changes for
  the same Issue ID can be in the same commit.

---

### Step 5: Post-Fix Verification

After fixing all occurrences of an Issue ID:

1. Re-read the modified lines — does the fix match the "Compliant" example?
2. Check the **Related Issues** list in the guide for secondary violations.
3. If `problems` tool is available: re-run and confirm the finding is gone
   and no new findings appeared.
4. For resource changes (`strings.xml`, `colors.xml`): verify the resource
   is referenced correctly — no `UnusedResources` introduced.

---

### Step 6: Suppression (Last Resort)

If a fix is technically impossible or the warning is a false positive:

**Kotlin — suppress annotation:**
```kotlin
@Suppress("UNCHECKED_CAST")
// Justification: Type-erased API from legacy Java interop; verified at runtime.
val items = intent.getSerializableExtra(KEY) as List<SensorData>
```

**Android Lint — suppress annotation:**
```kotlin
@SuppressLint("SetJavaScriptEnabled")
// Justification: WebView is internal-only, no external content loaded (spec §3.4).
fun setupWebView(webView: WebView) {
    webView.settings.javaScriptEnabled = true
}
```

**Lint XML baseline (whole-project, last resort):**
```bash
./gradlew lint --baseline lint-baseline.xml
```

**Rules for suppression:**
- Every `@Suppress` or `@SuppressLint` **must** have a justification comment.
- Bare `@Suppress` with no reason is not acceptable.
- Blanket `@file:Suppress(...)` at the top of a file requires a file-level
  justification comment explaining why the whole file is exempt.

---

### Step 7: Commit

One commit per Issue ID:

```
static(ui): fix HardcodedText in activity_main layout

Moved all hardcoded strings to strings.xml with proper i18n keys.
Post-fix: verified no UnusedResources introduced.
```

Commit type: `static` — see project commit convention.

---

## Quick Reference — Common Patterns Without a Guide

### HardcodedText — string literal in layout XML

```xml
<!-- ❌ -->
<TextView android:text="Hello World" />

<!-- ✅ -->
<TextView android:text="@string/welcome_message" />
<!-- Add to res/values/strings.xml:
     <string name="welcome_message">Hello World</string> -->
```

### NotifyDataSetChanged — RecyclerView adapter

```kotlin
// ❌ Invalidates entire list
adapter.notifyDataSetChanged()

// ✅ Targeted notification or DiffUtil
adapter.notifyItemChanged(position)
// Or use DiffUtil.calculateDiff() for structural changes
```

### UnusedResources — orphaned resource

```xml
<!-- ❌ Defined but never referenced -->
<color name="debug_color">#FF0000</color>

<!-- ✅ Remove the resource, or add a reference if it's needed -->
```

### WrongConstant — passing wrong IntDef value

```kotlin
// ❌ Passing raw int where @IntDef is expected
setVisibility(4)

// ✅ Use the correct named constant
setVisibility(View.GONE)
```

### VisibleForTesting scope leak

```kotlin
// ❌ Public only for tests — leaks API surface
public fun internalHelper(): Result { ... }

// ✅
@VisibleForTesting
internal fun internalHelper(): Result { ... }
```

---

## Cross-Issue Contamination Map

Common fix-triggers-new-issue patterns:

| Fix applied | Common new issue to check |
|---|---|
| Moved string to `strings.xml` (HardcodedText) | `UnusedResources` if old reference missed |
| Added `@SuppressLint` | Missing justification comment? |
| Changed `public` to `internal` (visibility) | Breaks companion object or Java interop? |
| Replaced `notifyDataSetChanged()` with targeted notify | Is position index in bounds? |
| Removed unused resource | Is it referenced via reflection or dynamic name? |
| Added null check for a previously non-null field | Introduces `Elvis` overuse (NullableBooleanElvis)? |

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

The step-by-step fix workflow is defined in the **Fix Workflow** section below.
Summary: run lint → fix one rule at a time → re-run to confirm count drops → commit per rule.


## Troubleshooting

- **Fix introduced a new violation** — re-run lint after each rule batch; revert and apply a narrower fix if needed.
- **`@SuppressLint` not taking effect** — place the annotation on the exact element (method, field, or class) that triggers the violation, not a parent.
- **Lint report is empty after `./gradlew lint`** — check the Gradle output for errors; try `./gradlew lintDebug` for a specific variant.
- **Cannot reproduce the violation locally** — ensure your local Android Studio lint version matches CI; update the `lint` tool or AGP version.


## References Folder Layout

```
references/
├── lint/        ← one .md per Android Lint Issue ID (e.g., HardcodedText.md)
├── kotlin/      ← one .md per Kotlin compiler warning key
└── detekt/      ← one .md per Detekt rule ID
```

Add a new rule guide whenever an issue is encountered for the first time.
Each rule guide file follows this template:

```markdown
# Lint Rule: <ISSUE-ID> — <short title>

## Rule Statement
What the rule checks and why it matters.

## Trigger Patterns
Code or resource patterns that cause a violation — with examples.

## Compliant Transformations
Exact transformation to apply — before/after samples.

## What NOT To Do
Wrong "fixes" that still violate this rule or introduce a new one.

## Post-Fix Verification Checklist
- [ ] Check these related rules after applying the fix.

## Suppression (if unavoidable)
Correct `@SuppressLint` or `@Suppress` annotation format.
```
