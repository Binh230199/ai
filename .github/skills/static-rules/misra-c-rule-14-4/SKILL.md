---
name: misra-c-rule-14-4
description: |
  Load when reviewing or fixing MISRA C:2012 Rule 14.4 violations (Boolean context in controlling expressions).
  Covers what "essentially Boolean" means, violation patterns for if/while/for conditions,
  compliant fix patterns with explicit comparisons, and special cases.
  Use when a commit message references MISRA Rule 14.4 or boolean context static analysis findings.
---

# MISRA C:2012 — Rule 14.4 (Boolean Context)

## Rule Summary
**Rule ID**: MISRA C:2012 Rule 14.4
**Category**: Control Statement Expressions
**Severity**: Required
**Rationale**: Using non-Boolean expressions in Boolean contexts (conditions of `if`, `while`, `do`-`while`, `for`) leads to unintended behavior when expression evaluates to non-zero non-one values.

> **Rule**: The controlling expression of an `if` statement and the controlling expression of an iteration statement shall be essentially Boolean.

---

## What "Essentially Boolean" Means

An expression is essentially Boolean if it is:
- The result of a relational operator: `==`, `!=`, `<`, `>`, `<=`, `>=`
- The result of a logical operator: `&&`, `||`, `!`
- A variable declared as `_Bool` or `bool` (C99/C++)
- The result of a function returning `bool` / `_Bool`

---

## Violations

```c
/* ❌ VIOLATION: integer used directly as condition */
int32_t errorCode = getStatus();
if (errorCode) {            /* Rule 14.4: not essentially Boolean */
    handleError();
}

/* ❌ VIOLATION: pointer used as condition */
uint8_t* buffer = getBuffer();
if (buffer) {               /* Rule 14.4: pointer, not Boolean */
    processBuffer(buffer);
}

/* ❌ VIOLATION: assignment result used as condition */
uint8_t byte;
while (byte = readNext()) { /* Rule 14.4: assignment, not Boolean */
    process(byte);
}

/* ❌ VIOLATION: bitwise AND used as condition */
uint32_t flags = getFlags();
if (flags & FLAG_READY) {   /* Rule 14.4: bitwise result, not Boolean */
    proceed();
}
```

---

## Compliant Patterns

```c
/* ✅ CORRECT: explicit comparison */
int32_t errorCode = getStatus();
if (errorCode != 0)  {
    handleError();
}

/* ✅ CORRECT: explicit null check */
uint8_t* buffer = getBuffer();
if (buffer != NULL) {
    processBuffer(buffer);
}

/* ✅ CORRECT: separate assignment and condition */
uint8_t byte = readNext();
while (byte != 0U) {
    process(byte);
    byte = readNext();
}

/* ✅ CORRECT: compare bitwise result to expected value */
uint32_t flags = getFlags();
if ((flags & FLAG_READY) == FLAG_READY) {
    proceed();
}

/* ✅ CORRECT: bool variable */
bool isReady = checkReadiness();
if (isReady) {              /* OK — isReady is essentially Boolean */
    proceed();
}
```

---

## How to Review for MISRA C Rule 14.4

When a commit message mentions "fix MISRA 14.4" or "fix MISRA C Rule 14.4":

1. **Locate all changed `if`, `while`, `do`, `for` controlling expressions** in the diff
2. **Classify each controlling expression** as essentially Boolean or not
3. **Verify the fix** converts non-Boolean to an explicit comparison using `==`, `!=`, relational operators
4. **Check for correct comparison value**:
   - Integer → compare to `0` or `0U` (e.g., `!= 0U`)
   - Pointer → compare to `NULL`
   - Bitfield/flags → compare result to the mask itself (e.g., `== FLAG_READY`)
5. **Check for unchanged nearby violations** — developers often fix only one occurrence, missing others in the same function

---

## Special Cases

```c
/* Accepted exception: boolean function return used directly */
bool isInitialized(void);
if (isInitialized()) { ... }  /* OK — return type is bool */

/* Accepted exception: logical NOT of essentially Boolean */
bool ok = process();
if (!ok) { ... }              /* OK — !bool is essentially Boolean */

/* NOT accepted: NOT of integer */
int32_t result = getValue();
if (!result) { ... }          /* ❌ VIOLATION — !integer is not essentially Boolean */
```

---

## Related Rules
- **MISRA C:2012 Rule 14.3**: Controlling expressions shall not be invariant
- **MISRA C:2012 Rule 10.1**: Operands shall not be of an inappropriate essential type
- **MISRA C:2012 Rule 10.5**: The value of an expression shall not be cast to an inappropriate essential type
