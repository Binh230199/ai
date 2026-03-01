---
name: lang-c-cpp
description: |
  Load when working with C or C++ code (.c, .cpp, .h, .hpp files) in an automotive embedded software project.
  Provides deep language context: RAII patterns, smart pointer usage, null guard patterns,
  fixed-width integer types, Doxygen comment templates, and common automotive anti-patterns to avoid.
  Use for code review, implementation, or any task involving C/C++ source files.
---

# C / C++ Language Context for Automotive Software

---

## C++ Patterns to Enforce

### RAII Pattern (Resource Acquisition Is Initialization)
```cpp
// ✅ Correct — resource managed by RAII
class FileHandle {
public:
    explicit FileHandle(const char* path) : m_fd(open(path, O_RDONLY)) {}
    ~FileHandle() { if (m_fd >= 0) close(m_fd); }
private:
    int m_fd;
};

// ❌ Wrong — manual resource management, leak-prone
int fd = open(path, O_RDONLY);
// ... (if exception or early return happens, close() never called)
close(fd);
```

### Smart Pointer Usage
```cpp
// ✅ Correct
std::unique_ptr<Sensor> sensor = std::make_unique<TemperatureSensor>(config);
sensor->init();  // no null check needed — unique_ptr guarantees non-null after make_unique

// ❌ Wrong — raw owning pointer
Sensor* sensor = new TemperatureSensor(config);
sensor->init();  // if init() throws, delete never called
delete sensor;
```

### Null Guard Pattern
```cpp
// ✅ Correct — always guard raw pointers
void process(const DataBuffer* buffer) {
    if (buffer == nullptr) {
        LOG_ERROR("process: null buffer received");
        return;
    }
    buffer->read();
}

// ❌ Wrong — no null check
void process(const DataBuffer* buffer) {
    buffer->read();  // UB if null
}
```

### Fixed-Width Integer Types
```cpp
// ✅ Correct — platform-independent sizes
uint8_t  byteValue  = 0xFFU;
int32_t  sensorData = 0;
uint64_t timestamp  = getMonotonicTimeNs();

// ❌ Wrong — size varies by platform
int   sensorData = 0;
long  timestamp  = 0;
```

### Enum Class for State/Error Codes
```cpp
// ✅ Correct — scoped, type-safe
enum class InitStatus : uint8_t {
    kSuccess = 0U,
    kTimeout = 1U,
    kHardwareFault = 2U
};

// ❌ Wrong — unscoped, implicit int
enum InitStatus { SUCCESS, TIMEOUT, HW_FAULT };
```

---

## Common Automotive C++ Anti-Patterns

| Anti-pattern | Why it's a problem | Preferred alternative |
|---|---|---|
| `dynamic_cast` without check | Crashes on failed cast | Always check result != nullptr |
| Exception in destructor | Undefined behavior if thrown during stack unwinding | Catch all in destructors, log only |
| `std::map` in real-time path | Memory allocation, non-deterministic | Use sorted `std::array` + binary search |
| `std::string` in ISR/safety path | Heap allocation | Fixed-size char buffer or `std::string_view` |
| `thread_local` without initialization | Subtle race on first access | Explicit initialization in thread start |

---

## Doxygen Comment Template (required for all public APIs)

```cpp
/**
 * @brief Short one-line description of what this function does.
 *
 * @details Extended description if needed. Explain preconditions,
 *          side effects, or important behavioral notes.
 *
 * @param[in]  paramName  Description of input parameter.
 * @param[out] resultPtr  Pointer to store the result; must not be null.
 * @return ErrorCode::kSuccess on success, ErrorCode::kTimeout if deadline exceeded.
 *
 * @note Thread-safe: protected by m_mutex.
 * @warning Must be called after init(), otherwise behavior is undefined.
 */
ErrorCode doSomething(uint32_t paramName, Result* resultPtr);
```

---

## Build / Compiler Flags Context (typical automotive project)
- Warnings treated as errors: `-Werror -Wall -Wextra -Wpedantic`
- Common additional flags: `-Wshadow -Wnull-dereference -Wdouble-promotion -Wformat=2`
- Sanitizers in debug: `-fsanitize=address,undefined`
- C++ standard: `-std=c++14` (AUTOSAR baseline)

When reviewing, flag patterns that would fail under these flags.
