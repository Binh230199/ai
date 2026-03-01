---
applyTo: "**/*.{c,cpp,h,hpp,cc,cxx}"
---

## Language: C / C++ — Always-On Context

These rules apply automatically to any file with C or C++ extensions.

### Standard & Guidelines
- Target standard: **C++14** (AUTOSAR C++14 compliant) or **C99/C11** for plain C files
- Follow **AUTOSAR C++14** guidelines for C++ code
- Follow **MISRA C:2012** rules for safety-critical C modules
- **Do not mix** C++ idioms into C-only files (`.c`, `.h`)

### Type Safety
- Use `<stdint.h>` / `<cstdint>` fixed-width types: `uint8_t`, `int32_t`, `uint64_t`
- Never use plain `int`, `char`, `long` in interface definitions or safety-critical paths
- Explicit casts required for narrowing conversions — no implicit narrowing
- Prefer `static_cast<>` over C-style casts in C++ code

### Memory Management
- **No raw `new`/`delete`** in C++ code — use RAII, `std::unique_ptr`, `std::shared_ptr`
- No dynamic memory allocation (`malloc`, `new`) in safety-critical or interrupt-service-routine paths
- Every raw pointer must be checked for null before dereference
- Resource acquisition must be exception-safe

### Null / Bounds Safety
- Guard every pointer dereference: `if (ptr != nullptr)` before use
- Array access must be bounds-checked; prefer `std::array` or `std::vector` over raw arrays
- No pointer arithmetic unless inside a dedicated, documented utility function

### Code Structure
- Every function/method must have a **Doxygen comment** (`/** */` style) in the header
- No magic numbers — use named constants (`constexpr`, `#define` with prefix, or `enum class`)
- No dead code, commented-out code blocks, or TODO left in committed code
- Function length: aim for < 50 lines; flag anything > 100 lines

### Error Handling
- Return codes must be checked — no silently ignored return values
- Prefer error enums (`enum class ErrorCode`) over raw integers for error states
- No `errno`-style globals for error propagation in new code

### Thread Safety
- Document thread-safety assumptions in the class/function Doxygen comment
- Shared mutable state must be protected: `std::mutex`, `std::atomic`, or explicit documentation
- No data races — flag any unsynchronized access to non-atomic shared variables

### Forbidden Patterns
- No `goto` statements
- No `#define` macros with side effects (use `inline constexpr` functions instead)
- No `using namespace std;` in header files
- No `reinterpret_cast` without explicit justification comment
- No `const_cast` except in documented legacy interop scenarios
