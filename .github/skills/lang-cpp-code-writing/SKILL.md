---
name: lang-cpp-code-writing
description: >
  Use when writing, reviewing, or refactoring C++ code (*.cpp, *.hpp, *.h)
  in an automotive embedded or Android NDK context (IVI, HUD, RSE on Linux/QNX/Android).
  Covers Modern C++11–17 idioms, SOLID principles, OOP design, RAII, smart pointers,
  move semantics, design patterns, Doxygen documentation, and a full pre-commit
  review checklist.
argument-hint: <class-or-module-name> [write|review|refactor]
---

# C++ Code Writing — Modern C++11–17

Expert-level best practices for writing production-quality Modern C++ on
Android Automotive / Linux / QNX platforms, guided by the principles of
Bjarne Stroustrup & Herb Sutter (C++ Core Guidelines), Scott Meyers
(Effective Modern C++), and Robert C. Martin (Clean Code).

Standards baseline: **C++17** (default) · **C++11** min ·

---

## When to Use This Skill

- Writing a new C++ class, module, or library from scratch.
- Reviewing a Gerrit patch that touches `.cpp` / `.hpp` files.
- Refactoring legacy C-style C++ to modern idioms.
- Choosing the right design pattern or ownership model for a component.
- Generating Doxygen class / method documentation.

---

## Prerequisites

- C++ standard confirmed: **C++17** (default), C++11 min.
- Compiler known: GCC 7+ cross-arm, Clang 6+, QCC for QNX.
- STL available (embedded: confirm `<memory>`, `<functional>` overhead is acceptable).
- AUTOSAR rule enforcement is out of scope here — use the `autosar-cpp14` skill.

---

## 1. File & Namespace Organization

> Goal: zero accidental symbol collisions; minimal compile-time coupling.

- Use `#pragma once` in every `.hpp` — cleaner than hand-rolled include guards.
- Wrap **every** public symbol in a namespace: `namespace Company::Module { ... }`. Never pollute the global namespace.
- Never put `using namespace std;` (or any `using namespace`) in a header.
- Place `using` aliases and `using namespace` inside **function scope** in `.cpp` only.
- Group includes: system `<...>` before project `"..."`, alphabetically within each group.
- One **public concept** per header. Hide implementation detail in `*_impl.hpp` or `.cpp`.
- Forward-declare instead of including where only a pointer / reference is needed — reduces compile times dramatically on large embedded projects.

```cpp
#pragma once

#include <cstdint>      // system
#include <memory>

#include "IAdcDriver.hpp"   // project

namespace Automotive::Sensor {
class TemperatureSensor { /* ... */ };
} // namespace Automotive::Sensor
```

---

## 2. Class Design & SOLID Principles

> Goal: classes that are easy to understand, test, extend, and replace independently.

### Single Responsibility (S)
- Each class has **one reason to change** — one job, one actor that owns it.
- If the class name contains "And", "Manager", or "Handler" spanning multiple domains, split it.
- Keep classes small enough that their public interface fits on one screen.

### Open / Closed (O)
- Extend behaviour by adding **new types or injected strategies**, not by editing existing classes.
- Prefer composition (`has-a`) over deep inheritance (`is-a`). Limit inheritance hierarchies to ≤ 3 levels.
- Use abstract interfaces (`class ISensor { virtual float read() = 0; }`) as extension points.

### Liskov Substitution (L)
- A derived class must honour **every contract** of its base: don't throw exceptions the base doesn't declare, don't weaken preconditions, don't strengthen postconditions.
- If substituting a derived class breaks callers, the inheritance is wrong — use composition instead.

### Interface Segregation (I)
- Prefer **narrow, role-based interfaces** over fat god-interfaces.
- A class that implements an interface should use every method in it.

```cpp
// GOOD — two focused interfaces
class IReadable { public: virtual float read() const = 0; virtual ~IReadable() = default; };
class IWritable { public: virtual void  write(float v)  = 0; virtual ~IWritable() = default; };

// BAD — forces all implementors to provide calibrate/log/reset even if irrelevant
class ISensorGod { /* read, write, calibrate, log, reset, … */ };
```

### Dependency Inversion (D)
- High-level modules must not depend on low-level modules. Both depend on **abstractions**.
- Inject dependencies through the **constructor** — never instantiate concrete collaborators inside a class body.
- Interfaces belong to the **caller's** package, not the implementer's.

```cpp
// GOOD — ThermalMonitor depends only on the ISensor abstraction
class ThermalMonitor {
public:
    explicit ThermalMonitor(std::shared_ptr<ISensor> sensor)
        : m_sensor{std::move(sensor)} {}
private:
    std::shared_ptr<ISensor> m_sensor;   // injected; mockable in tests
};
```

---

## 3. Ownership, RAII & Smart Pointers

> "Resource acquisition is initialisation" — every resource has a clear, automatic lifetime.

- **Never use raw `new` / `delete`** — use `std::make_unique` / `std::make_shared`.
- Express ownership intent explicitly with types:

| Ownership intent | Type | When |
|---|---|---|
| Sole ownership | `std::unique_ptr<T>` | default choice for heap objects |
| Shared ownership | `std::shared_ptr<T>` | only when multiple owners are genuinely needed |
| Non-owning observer | `T&` or `T*` (document it) | lifetime guaranteed by caller |
| Factory result | `std::unique_ptr<T>` from `make_unique` | returned from factory functions |

- Prefer **Rule of Zero**: let compiler-generated special members handle cleanup by composing RAII members (`unique_ptr`, `vector`, `fstream`, etc.). No destructor needed.
- Apply **Rule of Five** only when a class directly manages a raw resource (HW handle, fd). Define or `= delete` all five together.
- Mark single-argument constructors `explicit` — prevents accidental implicit conversions.
- Base class destructor must be `virtual` for polymorphic bases, or `protected` non-virtual for CRTP / non-polymorphic bases.
- Use the member initialiser list; avoid assignment in the constructor body.

```cpp
class TemperatureSensor {
public:
    explicit TemperatureSensor(std::uint8_t channel,
                               std::unique_ptr<IAdcDriver> driver);
    ~TemperatureSensor();
    TemperatureSensor(const TemperatureSensor&)            = delete;
    TemperatureSensor& operator=(const TemperatureSensor&) = delete;
    TemperatureSensor(TemperatureSensor&&)                 noexcept;
    TemperatureSensor& operator=(TemperatureSensor&&)      noexcept;

    [[nodiscard]] std::optional<float> readDegC() const;

private:
    std::uint8_t                m_channel;
    std::unique_ptr<IAdcDriver> m_driver;   // RAII: auto-released on destruction
};
```

---

## 4. Modern C++ Idioms (C++11–17)

> Prefer language features that eliminate entire classes of bugs at zero runtime cost.

- **{}** — use uniform initialisation to prevent narrowing conversions and unify syntax for all types.
- **`auto`** — use when the type is obvious, verbose, or an iterator. Avoid when it hides important type information at a code review.
- **`constexpr`** — prefer over `#define` for compile-time constants; also `constexpr` functions where possible.
- **`[[nodiscard]]`** — mark every factory, error-returning, and query function. Prevents silently discarded results.
- **Scoped enums** — always `enum class`, never plain `enum`, to prevent implicit int conversions.
- **Range-based `for`** — `for (const auto& x : container)` instead of index loops when the index is not needed.
- **Structured bindings (C++17)** — `auto [val, ok] = map.emplace(k, v);` — no more `.first`/`.second`.
- **`if`-with-initialiser (C++17)** — `if (auto it {m.find(k)}; it != m.end())` — scopes the variable to the condition.
- **`std::optional<T>`** — express "no value" explicitly; replace sentinel values (`-1`, `nullptr`) in return types.
- **`std::variant<Ts…>`** — type-safe union. Use instead of tagged unions or `void*`.
- **`std::string_view`** — accept string parameters as `std::string_view` to avoid copies (C++17).
- **Lambdas** — capture minimally; prefer `[&]` only in short, immediately-invoked contexts. Capture by value `[=]` when the lambda outlives the surrounding scope.

```cpp
constexpr std::uint32_t kTimeoutMs {100U};          // not: #define TIMEOUT 100

[[nodiscard]] std::optional<float> tryReadDegC() const noexcept;

enum class SensorState : std::uint8_t { Idle, Active, Fault };

for (const auto& frame : m_rxQueue) { process(frame); }

if (auto it {m_cache.find(id)}; it != m_cache.end()) {
    return it->second;
}
```

---

## 5. Value Semantics & Move Semantics

> Design types to be cheap to move. Copy only when genuinely needed.

- Declare move constructor and move assignment **`noexcept`** — enables `std::vector` reallocation to use move instead of copy.
- **Sink parameter pattern**: take by value, then `std::move` into the member — one overload handles both l-value (copy) and r-value (move) callers.
- **`const T&`** for read-only access to non-trivial types.
- **By value** for cheap types (`int`, `float`, small POD ≤ 2 pointers).
- **`T&&`** only in forwarding templates (`template<typename T> void f(T&&)`).
- Never use a moved-from object — treat it as valid but **unspecified** state.
- Prefer value semantics (return by value) over output parameters where the type is cheap to move.

```cpp
// Sink pattern — constructor accepts both lvalue (copied in) and rvalue (moved in)
explicit Buffer(std::vector<std::uint8_t> data) noexcept
    : m_data{std::move(data)} {}
```

---

## 6. Error Handling

> Choose one strategy per module boundary. Never mix strategies silently.

| Context | Strategy | Rationale |
|---|---|---|
| Application / framework layer | **Exceptions** (`std::runtime_error`, domain types) | Propagation is automatic; no ignored returns |
| HAL / driver / ASIL path | **`std::optional<T>` or `enum class` error** | `noexcept` required; exceptions may be disabled |
| Interop with C layer | **Error enum + output parameter** | C ABI compatibility |
| Programming-error preconditions | **`assert` in debug; throw in release** | Fail-fast; not recoverable by caller |

- Never use `int` return with magic sentinels — use a typed `enum class ErrorCode`.
- Mark functions that cannot fail `noexcept` — it is a contract, not just an optimisation hint.
- Document the error strategy in the class Doxygen block so every caller knows what to expect.
- Return `std::optional<T>` or `tl::expected<T, E>` for operations that can legitimately fail without that being a programming error.
- Never discard a `[[nodiscard]]` return value without a comment explaining why.

```cpp
// HAL path — noexcept, no exceptions, optional as the failure channel
[[nodiscard]] std::optional<float> TemperatureSensor::tryReadDegC() const noexcept {
    if (!m_driver) { return std::nullopt; }
    const auto raw {m_driver->readChannel(m_channel)};
    if (!raw) { return std::nullopt; }
    return convertAdcToTemp(*raw);
}
```

---

## 7. Concurrency & Thread Safety

> Design for correctness first. Measure before optimising.

- Document the thread-safety contract of every class in a `@thread_safety` Doxygen tag.
- Protect shared mutable state with `std::mutex` + `std::lock_guard` / `std::scoped_lock`.
- Mark `m_mutex` as `mutable` so it can be locked inside `const` methods without breaking const-correctness.
- Use `std::atomic<T>` for simple shared flags and counters — cheaper than a mutex and lock-free.
- Never hold a mutex across blocking I/O or long operations — minimise critical section size.
- Prefer **message-passing / queues** over shared memory for cross-thread communication (on QNX: use native pulses / message-passing).
- `volatile` is only for memory-mapped registers and ISR-shared flags — it is **not** a synchronisation primitive.
- Use `std::call_once` / Meyers singleton (`static Local inst;`) for thread-safe one-time initialisation (C++11 guarantees static local init is race-free).

```cpp
class SensorCache {
public:
    /** @thread_safety  Safe for concurrent readers and a single writer. */
    void          update(float value) { std::lock_guard lock{m_mutex}; m_latest = value; }
    [[nodiscard]] float latest() const { std::lock_guard lock{m_mutex}; return m_latest; }
private:
    mutable std::mutex m_mutex;
    float              m_latest{0.0F};
};
```

---

## 8. Design Patterns

> Pick the simplest pattern that solves the problem. Over-engineering is a defect.

### Creational

| Pattern | When to use | Modern C++ idiom |
|---|---|---|
| **Factory Method** | Decouple creation from use; callers don't know or care about the concrete type | Pure virtual `create()` returning `unique_ptr<IProduct>` |
| **Abstract Factory** | Families of related objects that vary by platform (sensor suite per SoC) | Interface with multiple `make*()` methods |
| **Builder** | Object with many optional / validated parameters; telescoping-constructor smell | Method-chaining `Builder`; `build()` validates and returns product |
| **Singleton** | Single process-wide resource (logger, config). Prefer injection; use sparingly | Meyers Singleton: `static Local inst;` + deleted copy/move |

### Structural

| Pattern | When to use | Modern C++ idiom |
|---|---|---|
| **PIMPL** | Reduce compile-time coupling; stable binary ABI | `struct Impl; std::unique_ptr<Impl> m_impl;` defined in `.cpp` |
| **Adapter** | Wrap an incompatible legacy C API behind a modern C++ interface | Class wrapping legacy handle, implementing `IFoo` |
| **Facade** | Single clean entry point into a complex subsystem | One class delegating to internal components; hides subsystem headers |
| **Decorator** | Add cross-cutting behaviours (logging, retry, metrics) without subclassing | Owns `shared_ptr<IBase>`, forwards all calls and augments selectively |

### Behavioural

| Pattern | When to use | Modern C++ idiom |
|---|---|---|
| **Strategy** | Swap algorithm at runtime without touching the host class | Inject `std::function<R(Args…)>` or `unique_ptr<IStrategy>` |
| **Observer** | Decouple an event source from N interested listeners | Register `std::function` callbacks into a `std::vector` |
| **State** | Object's behaviour changes entirely based on current state | `std::unique_ptr<IState>` swapped on transitions |
| **Command** | Encapsulate an operation as a first-class object (queue, undo) | `std::function<void()>` — zero overhead for simple cases |
| **Template Method** | Fixed algorithm skeleton; individual steps customised by subclass | Non-virtual public driver + `virtual` protected `doStep()` hooks |

```cpp
// PIMPL — stable ABI; callers never see Impl headers
class CanController {
public:
    explicit CanController(std::uint8_t busId);
    ~CanController();           // defined in .cpp — Impl is incomplete here
    [[nodiscard]] bool sendFrame(const CanFrame& frame);
private:
    struct Impl;
    std::unique_ptr<Impl> m_impl;
};

// Strategy — inject behaviour; avoids hard-coded subclassing
class SensorFilter {
public:
    using Fn = std::function<float(float)>;
    explicit SensorFilter(Fn fn) : m_fn{std::move(fn)} {}
    [[nodiscard]] float apply(float raw) const { return m_fn(raw); }
private:
    Fn m_fn;
};
```

---

## 9. Architecture & Clean Boundaries

> High-level policy must not depend on low-level detail (Dependency Rule — Robert C. Martin).

- Organise code in layers: **Domain → Use Cases → Interface Adapters → Infrastructure**.
- Domain entities and interfaces live in the innermost layer — they have **zero external dependencies**.
- Infrastructure (drivers, HAL, network stacks) always depends inward; never the reverse.
- Apply the **Anti-Corruption Layer** pattern at subsystem boundaries — wrap a legacy C HAL with a C++ interface so domain code never sees raw C types.
- Enforce **bounded contexts**: a `Sensor` in the thermal subsystem is not the same type as a `Sensor` in diagnostics — do not share types across contexts to avoid accidental coupling.
- Keep public headers **lean**: expose only what callers need; hide everything behind PIMPL or `detail` namespaces.

---

## 10. Documentation (Doxygen)

> If the intent is not obvious from the code alone, document it before writing the code.

- Every public class needs a `/** @brief … */` block stating what it represents.
- Every public method needs `@brief`, `@param[in/out]`, `@return`, `@pre`, `@post`, `@throws` (as applicable).
- `@thread_safety` tag on every class and on methods with non-obvious threading behaviour.
- `@details` for non-trivial algorithms or design decisions — explain **why**, not **what**.

```cpp
/**
 * @brief  Read the current temperature from the NTC sensor.
 *
 * @return Temperature in °C, or std::nullopt on hardware error.
 *
 * @pre    Object was successfully constructed (driver != nullptr, channel 0–7).
 * @post   Returned value, when present, is in range [–40, 125] °C.
 * @thread_safety  Safe for concurrent callers after construction.
 */
[[nodiscard]] std::optional<float> readDegC() const noexcept;
```

---

## Step-by-Step Workflows

### Step 1: Set up file structure
Create `.hpp` (declarations) and `.cpp` (definitions) pairs; add `#pragma once` to headers.

### Step 2: Design the class
Apply the Rule of Zero/Five; mark copy/move constructors as `= default` or `= delete` explicitly.

### Step 3: Apply the patterns from this skill
Follow sections 1–10 below in order: naming → ownership → modern C++ → error handling, etc.

### Step 4: Run static analysis
Run `clang-tidy` with `cppcoreguidelines-*` and `modernize-*` checks; fix all reported violations.

### Step 5: Write unit tests
Every public method needs a gtest covering the happy path and at least one error path.


## Pre-Commit Review Checklist

Before pushing to Gerrit, verify:

**File & namespace**
- [ ] `#pragma once` in every header
- [ ] Every public symbol inside a namespace
- [ ] No `using namespace` in any header

**Class design**
- [ ] Each class has a single, clearly stated responsibility
- [ ] Single-argument constructors are `explicit`
- [ ] Rule of Zero or Rule of Five applied consistently
- [ ] Base class destructor is `virtual` (polymorphic) or `protected` non-virtual

**Ownership & memory**
- [ ] No raw `new` / `delete` — `make_unique` / `make_shared` used throughout
- [ ] No owning raw pointers that lack a RAII wrapper

**Modern C++**
- [ ] No magic numbers — `constexpr` named constants used
- [ ] `[[nodiscard]]` on all factory, query, and error-returning functions
- [ ] `enum class` used; no plain `enum`
- [ ] Move constructor and assignment declared `noexcept`

**Error handling**
- [ ] Error strategy documented in class Doxygen block
- [ ] No silently ignored return values

**Concurrency**
- [ ] Thread-safety contract documented with `@thread_safety`
- [ ] Shared mutable state protected by `std::mutex` or `std::atomic`

**Documentation**
- [ ] Every public class has `@brief`
- [ ] Every public method has `@brief`, `@param`, `@return`; `@pre`/`@post` where relevant

---

## Examples

See companion files:
- [good_temperature_sensor.hpp](./examples/good_temperature_sensor.hpp) — well-structured class with DI, RAII, `[[nodiscard]]`
- [good_temperature_sensor.cpp](./examples/good_temperature_sensor.cpp) — implementation with move semantics and `std::optional`
- [bad_sensor.cpp](./examples/bad_sensor.cpp) — C-style anti-patterns annotated line by line

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `use of deleted function` on copy | Rule of Five: destructor defined but copy not | Delete copy or implement all five |
| Linker: `undefined reference to vtable` | Out-of-line virtual destructor missing | Define destructor in `.cpp` |
| Object sliced when passed by value | Polymorphic type passed as value | Pass by reference or `shared_ptr<Base>` |
| `std::bad_weak_ptr` at runtime | `shared_from_this()` called before `shared_ptr` wraps object | Always construct via `make_shared` |
| Bloated binary from templates | Template instantiated in every TU | Explicit instantiation in one `.cpp` |
| `lock_guard` error on `const` method | Mutex not `mutable` | Declare mutex field `mutable` |

---

## References

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) — Stroustrup & Sutter
- [Effective Modern C++](https://www.oreilly.com/library/view/effective-modern-c/9781491908419/) — Scott Meyers
- [cppreference.com](https://en.cppreference.com/) — C++17 standard library reference
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) — Robert C. Martin
- Internal skill: [lang-c-code-writing](../lang-c-code-writing/SKILL.md) — pure C modules in the same codebase
