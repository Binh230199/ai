---
name: autosar-m5-0-2
description: |
  Load when reviewing or fixing AUTOSAR C++14 Rule M5-0-2 violations (narrowing conversions).
  Covers what the rule prohibits, compliant fix patterns using static_cast<> with range checks,
  common false fixes to reject (C-style casts, reinterpret_cast), and how to verify completeness.
  Use when a commit message references AUTOSAR M5-0-2 or narrowing conversion static analysis findings.
---

# AUTOSAR C++14 — Rule M5-0-2 (Narrowing Conversions)

## Rule Summary
**Rule ID**: AUTOSAR C++14 M5-0-2
**Category**: Type Safety
**Severity**: Required
**Rationale**: Implicit narrowing conversions can silently truncate values, leading to incorrect behavior in safety-critical systems.

> **Rule**: The operands of an operator shall not be of a type that is potentially evaluated and is not value-preserving.

---

## What This Rule Prohibits

Any implicit conversion where the destination type cannot represent all values of the source type:

```cpp
// ❌ VIOLATION: int32_t → uint8_t (narrowing, potential data loss)
int32_t sensorValue = 300;
uint8_t byteVal = sensorValue;  // M5-0-2: 300 does not fit in uint8_t

// ❌ VIOLATION: double → float (precision loss)
double precise = 3.14159265358979;
float approx = precise;  // M5-0-2: precision loss

// ❌ VIOLATION: int → bool (non-boolean to boolean)
int32_t count = getItemCount();
bool hasItems = count;  // M5-0-2: use explicit comparison instead

// ❌ VIOLATION: signed → unsigned implicit
int32_t signedVal = -1;
uint32_t unsignedVal = signedVal;  // M5-0-2: wraps to UINT32_MAX
```

---

## Compliant Patterns

```cpp
// ✅ CORRECT: explicit cast + range check
int32_t sensorValue = getSensorValue();
if (sensorValue >= 0 && sensorValue <= 255) {
    uint8_t byteVal = static_cast<uint8_t>(sensorValue);
    processBuffer(byteVal);
} else {
    LOG_ERROR("Sensor value out of range: %d", sensorValue);
}

// ✅ CORRECT: explicit comparison for bool conversion
int32_t count = getItemCount();
bool hasItems = (count > 0);

// ✅ CORRECT: explicit cast for float conversion (with acknowledged precision loss)
double precise = computeAngle();
float approx = static_cast<float>(precise);  // explicit, acknowledged

// ✅ CORRECT: use same-width types to avoid conversion altogether
uint32_t source = getSource();
uint32_t dest   = source;  // no conversion, no issue
```

---

## How to Review for M5-0-2

When a commit message mentions "fix static M5-0-2" or "fix AUTOSAR M5-0-2":

1. **Find all changed lines** in the diff
2. **Check each assignment and function call argument** for implicit type mismatch
3. **Verify the fix pattern**:
   - Is there a range check before the cast?
   - Is `static_cast<>` used (not C-style cast)?
   - Is there error handling for out-of-range values?
4. **Check surrounding context** — sometimes fixing one narrowing reveals another nearby
5. **Verify no regression**: make sure the fix doesn't widen scope unnecessarily

---

## Common False Patterns to Reject

```cpp
// ❌ Still a violation — C-style cast does not fix M5-0-2, it just silences the warning
uint8_t val = (uint8_t)sensorValue;  // WRONG fix

// ❌ Still a violation — reinterpret_cast is even worse
uint8_t val = *reinterpret_cast<uint8_t*>(&sensorValue);  // dangerous

// ✅ Only static_cast<> WITH range validation is the correct fix
```

---

## Related Rules
- **M5-0-3**: Casts shall not remove const or volatile qualification
- **M5-0-4**: An implicit integral conversion shall not change the signedness
- **M5-0-6**: An implicit integral or floating-point conversion shall not reduce the size of the underlying type
