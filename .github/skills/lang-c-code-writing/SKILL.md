---
name: lang-c-code-writing
description: >
  Use when writing, reviewing, or refactoring C code (*.c, *.h) in an
  automotive embedded context (IVI, HUD, RSE on Linux/QNX).
  Covers MISRA C:2012 compliance, fixed-width types, null/bounds safety,
  memory management without dynamic allocation in critical paths, Doxygen
  documentation, error-code patterns, and a full pre-commit review checklist.
argument-hint: <file-or-module-name> [write|review|refactor]
---

# C Code Writing — Automotive Embedded

A senior embedded engineer's complete mental checklist for writing and reviewing
production-quality C code on Android Automotive / Linux / QNX platforms.
Standards baseline: **C99 / C11** + **MISRA C:2012** (mandatory rules).

---

## When to Use This Skill

- Writing a new `.c` / `.h` module from scratch.
- Reviewing a pull request / Gerrit patch that touches C files.
- Refactoring legacy C code to meet MISRA or AUTOSAR quality gates.
- Resolving Coverity or static-analysis findings in C files.
- Generating Doxygen-ready file/function headers.

---

## Prerequisites

- Target standard confirmed: **C99** or **C11** (default: C11).
- Safety classification known: **QM / ASIL-A…D** (affects required rule set).
- Compiler and platform known (GCC cross-arm, QCC for QNX, etc.).
- `<stdint.h>` and `<stdbool.h>` available on the target toolchain.

---

## Step-by-Step Workflow

### Step 1 — File & Header Structure

Every `.h` file must have an include guard and a Doxygen file block:

```c
/**
 * @file   sensor_driver.h
 * @brief  Public interface for the temperature sensor driver.
 *
 * @details
 *   Provides initialise / read / deinitialise operations for the NTC
 *   sensor attached to ADC channel 3.  Thread-safe when used with a
 *   single reader and single writer; concurrent writers require external
 *   locking.
 *
 * @author  <author>
 * @date    2026-03-14
 */

#ifndef SENSOR_DRIVER_H
#define SENSOR_DRIVER_H

#include <stdint.h>
#include <stdbool.h>

/* ... declarations ... */

#endif /* SENSOR_DRIVER_H */
```

- One concept per header — do **not** bundle unrelated APIs.
- No function definitions in headers (inline allowed only for trivial accessors).
- System includes (`< >`) before project includes (`" "`), alphabetically sorted.

---

### Step 2 — Type Selection

| Situation | Use | Never use |
|---|---|---|
| Integer with known width | `uint8_t`, `int32_t`, `uint64_t` | `int`, `long`, `char` (in interfaces) |
| Boolean flag | `bool` (`<stdbool.h>`) | `int`, `#define TRUE 1` |
| Bit-field / register map | `uint8_t : 3;` with explicit underlying type | unnamed bitfields, `int : 3` |
| Function pointer | `typedef RetType (*FuncName_t)(ParamType);` | raw function pointers without typedef |
| Size / count | `size_t` | `int`, `unsigned` |
| Pointer to opaque handle | `typedef struct Tag *Handle_t;` | `void *` in public APIs |

> **MISRA C:2012 Rule 10.1 — 10.4**: Operands must have appropriate essential type;
> no implicit conversions between signed/unsigned.

---

### Step 3 — Function Design

```c
/**
 * @brief  Read the current temperature from the NTC sensor.
 *
 * @param[out] pTemperature_degC  Pointer to store the result in °C.
 *                                Must not be NULL.
 * @return ::SensorError_t  SENSOR_OK on success, error code otherwise.
 *
 * @pre   Sensor_Init() must have been called successfully.
 * @post  *pTemperature_degC is valid only when SENSOR_OK is returned.
 * @thread_safety  Safe for single-reader, single-writer; see file header.
 */
SensorError_t Sensor_ReadTemperature(int16_t * const pTemperature_degC);
```

Rules:
- **One responsibility** per function; aim for < 50 executable lines.
- **Every parameter** that is a pointer: annotate `[in]`, `[out]`, or `[in,out]`.
- **Output pointers** must be checked for NULL at function entry:
  ```c
  if (pTemperature_degC == NULL) { return SENSOR_ERR_NULL_PTR; }
  ```
- **No side effects** via global state without explicit documentation.
- Naming: `Module_ActionNoun()` — `Sensor_ReadTemperature`, `Can_SendFrame`.

---

### Step 4 — Error Handling

Define a module-specific error enum — never return raw integers:

```c
/** @brief Return codes for the Sensor module. */
typedef enum
{
    SENSOR_OK            = 0,   /**< Operation completed successfully. */
    SENSOR_ERR_NULL_PTR  = 1,   /**< Caller passed a NULL pointer.    */
    SENSOR_ERR_NOT_INIT  = 2,   /**< Module not initialised.          */
    SENSOR_ERR_TIMEOUT   = 3,   /**< Hardware did not respond in time. */
    SENSOR_ERR_HW_FAULT  = 4    /**< Unrecoverable hardware error.    */
} SensorError_t;
```

Pattern at call sites — **always** check return values:

```c
SensorError_t err = Sensor_ReadTemperature(&temp);
if (err != SENSOR_OK)
{
    Log_Error("Sensor_ReadTemperature failed: %d", (int32_t)err);
    return MY_MODULE_ERR_SENSOR;   /* propagate; never silently ignore */
}
```

> **MISRA C:2012 Rule 17.7**: The return value of a non-void function shall be used.

---

### Step 5 — Memory & Resource Management

| Rule | Rationale |
|---|---|
| No `malloc` / `calloc` / `free` in ISR or safety-critical paths | Heap is non-deterministic |
| Use static or stack allocation for known-size objects | Deterministic lifetime |
| If heap is needed (QM paths only), always check return: `if (ptr == NULL)` | OOM must be handled |
| Pair every resource acquisition with a release in the same scope or documented owner | Prevent leaks |
| Zero-initialise static buffers: `static uint8_t buf[64] = {0U};` | Avoid stale data |

```c
/* GOOD — static allocation with explicit size constant */
#define SENSOR_BUFFER_SIZE  (64U)
static uint8_t s_rxBuffer[SENSOR_BUFFER_SIZE] = {0U};

/* BAD — VLA, forbidden by MISRA C:2012 Rule 18.8 */
uint8_t buffer[n];   /* n is a runtime variable */
```

---

### Step 6 — Null & Bounds Safety

```c
/* Guard every pointer before use */
void Process_Frame(const uint8_t * const pData, uint16_t length)
{
    if ((pData == NULL) || (length == 0U))
    {
        return;   /* or return error code */
    }

    for (uint16_t i = 0U; i < length; i++)
    {
        /* safe: i is bounds-checked */
        DoWork(pData[i]);
    }
}
```

- **No pointer arithmetic** outside a dedicated, named utility function.
- `sizeof` on pointer vs. array: always use the array name, not a pointer to it.
- String operations: prefer `strncpy` / `snprintf` with explicit size; never `strcpy` / `sprintf`.

---

### Step 7 — Constants & Magic Numbers

```c
/* GOOD */
#define ADC_VREF_MV         (3300U)   /**< ADC reference voltage in mV. */
static const uint8_t  K_MAX_RETRIES = 3U;
static const uint32_t K_TIMEOUT_MS  = 100UL;

/* BAD */
if (retries > 3)      /* magic number */
if (voltage < 3300)   /* undocumented constant */
```

- `#define` constants: **ALL_CAPS**, bracketed, with `U`/`UL` suffix for unsigned.
- `static const` preferred over `#define` when type matters.
- `enum` for grouped symbolic values (state-machine states, event IDs).

---

### Step 8 — MISRA C:2012 Priority Checklist

Work through this before submitting to Coverity / static-analysis:

| # | Rule | What to check |
|---|---|---|
| 1 | **14.4** | Boolean context — only genuine `bool` or comparison in `if`/`while` |
| 2 | **10.1–10.4** | No implicit arithmetic conversions; explicit casts with justification |
| 3 | **17.7** | Every non-void return value used |
| 4 | **15.5** | Single exit point per function (or document deliberate multiple returns) |
| 5 | **13.5** | No side-effects in right-hand operand of `&&` / `\|\|` |
| 6 | **18.8** | No VLAs |
| 7 | **21.3** | No `malloc`/`free` (or justified & reviewed) |
| 8 | **11.3** | No cast between pointer and non-pointer |
| 9 | **8.7** | File-scope objects used only in one function → declare `static` |
| 10 | **2.2** | No dead code |

For known required deviations, add a deviation comment:
```c
/* MISRA C:2012 Rule 11.3 deviation — required for HW register map cast,
   reviewed and approved in safety analysis SA-2024-007. */
pReg = (volatile Reg_t *)(uint32_t)BASE_ADDR;  /* NOLINT */
```

---

### Step 9 — Thread Safety & Concurrency

```c
/* Document assumptions at the top of the .c file */
/**
 * @section thread_safety Thread Safety
 *   - Sensor_Init() / Sensor_Deinit(): must be called from a single
 *     initialisation thread only.
 *   - Sensor_ReadTemperature(): safe for concurrent readers; internal
 *     state is read-only after init.
 *   - Sensor_Calibrate(): NOT thread-safe; caller must hold s_moduleMutex.
 */
```

- Shared mutable state → protect with `pthread_mutex_t` or platform equivalent.
- Prefer **message passing / queue** over shared memory in RTOS contexts (QNX pulses).
- `volatile` for memory-mapped registers and ISR-shared flags; it is **not** a synchronisation primitive.

---

### Step 10 — Review Checklist

- [ ] Include guard present and unique (`MODULE_FILE_H`)
- [ ] Doxygen `@file` block in every `.h`; `@brief` on every public symbol
- [ ] All parameters annotated `[in]` / `[out]` / `[in,out]`
- [ ] Every pointer checked for NULL at function entry
- [ ] No `malloc`/`free` in ISR or ASIL paths (or deviation documented)
- [ ] No magic numbers — all literals named
- [ ] All return values checked
- [ ] No VLAs (`uint8_t buf[n]` where `n` is runtime)
- [ ] No implicit integer conversions across sign boundary
- [ ] File-scope variables are `static` unless deliberately exported
- [ ] No `goto`, no dead code, no commented-out blocks
- [ ] Thread-safety assumptions documented
- [ ] MISRA deviations commented with justification and deviation ID

---

## Pre-Commit Checklist

- [ ] Include guard present and unique (`MODULE_FILE_H`)
- [ ] Doxygen `@file` in every `.h`; `@brief` on every public symbol; all params annotated `[in]`/`[out]`
- [ ] Every pointer checked for `NULL` at function entry
- [ ] All return values checked — no silently ignored error codes
- [ ] No `malloc`/`free` in ISR or ASIL paths (or deviation documented)
- [ ] No magic numbers — all literals named with `#define` or `enum`
- [ ] No implicit integer conversions across sign boundary (`-Wsign-compare` clean)
- [ ] No VLAs (`uint8_t buf[n]` where `n` is runtime-determined)
- [ ] File-scope variables declared `static` unless deliberately exported
- [ ] No `goto`, no unreachable code, no commented-out blocks
- [ ] Thread-safety assumptions documented in Doxygen
- [ ] MISRA deviations annotated with justification comment and deviation ID
- [ ] Compiles with `0 warnings` under `-Wall -Wextra -Wpedantic`

---

## Examples

### Good — Defensive function with error enum

```c
/* See examples/good_sensor_read.c */
SensorError_t Sensor_ReadTemperature(int16_t * const pTemperature_degC)
{
    if (pTemperature_degC == NULL)
    {
        return SENSOR_ERR_NULL_PTR;
    }

    if (!s_isInitialised)
    {
        return SENSOR_ERR_NOT_INIT;
    }

    uint16_t rawAdc = Adc_ReadChannel(ADC_CHANNEL_NTC);
    *pTemperature_degC = Convert_AdcToTemp(rawAdc);

    return SENSOR_OK;
}
```

### Bad — Raw int return, unchecked pointer, magic number

```c
/* BAD: multiple violations */
int readTemp(int16_t *t)          /* no fixed-width type on return */
{
    *t = adc_read(3) * 100 / 4096; /* NULL not checked; magic numbers */
    return 0;                       /* return value meaning not documented */
}
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Coverity: `MISRA_CAST` | Implicit narrowing in assignment | Add explicit cast + deviation comment |
| Coverity: `NULL_RETURNS` | Missing null check after function return | Add `if (ptr == NULL)` guard |
| Coverity: `DEAD_CODE` | Unreachable branch | Remove dead branch; check logic |
| GCC: `-Wsign-compare` | Signed/unsigned comparison | Cast to common unsigned type |
| GCC: `-Wimplicit-function-declaration` | Missing `#include` | Add the correct header |
| Linker: multiple definition | Function defined in `.h` | Move to `.c`, declare `extern` in `.h` |

---

## References

- [MISRA C:2012 — MISRA Consortium](https://www.misra.org.uk/misra-c/)
- [Coverity Static Analysis](https://scan.coverity.com/)
- [AUTOSAR C++14 Guidelines](https://www.autosar.org/fileadmin/standards/R22-11/AP/AUTOSAR_RS_CPP14Guidelines.pdf)
