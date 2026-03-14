---
name: cpp-memory-management
description: >
  Use when writing, reviewing, or refactoring C++ code involving memory ownership,
  lifetime management, smart pointers, RAII, custom allocators, or memory safety
  in automotive embedded projects (IVI, HUD, RSE on Linux/QNX/Android NDK).
  Covers Rule of Zero/Five, unique_ptr/shared_ptr, weak_ptr, placement new,
  arena allocators, AddressSanitizer, and common memory bug patterns.
argument-hint: <class-or-module> [write|review|audit]
---

# C++ Memory Management — Embedded Automotive

Expert practices for safe, deterministic, and efficient memory management in
**C++14–C++20** embedded automotive code running on **Linux**, **QNX**, and **Android NDK**.

---

## When to Use This Skill

- Designing ownership model for a new class or subsystem.
- Reviewing code for raw pointer misuse, leaks, or dangling references.
- Replacing manual `new`/`delete` with RAII idioms.
- Designing a component that must avoid heap allocation in real-time paths.
- Auditing code for MISRA C++ violations related to memory.
- Investigating a crash suspected to be a use-after-free or heap corruption.

---

## Ownership Vocabulary

| Concept | Meaning |
|---|---|
| **Owner** | Entity responsible for deleting the resource |
| **Non-owning pointer/reference** | Observes but never deletes |
| **Unique ownership** | Exactly one owner (`std::unique_ptr`) |
| **Shared ownership** | Multiple owners via reference counting (`std::shared_ptr`) |
| **Weak reference** | Observes shared-owned resource without extending lifetime (`std::weak_ptr`) |

**Rule of thumb**: 99% of C++ code should have zero explicit `delete` calls. Use smart pointers.

---

## The Rule of Zero / Three / Five

```cpp
// ── Rule of Zero (preferred) ─────────────────────────────────────
// If your class uses ONLY smart pointers / standard containers,
// let the compiler generate everything:
class AudioTrack {
    std::string             name_;
    std::vector<int16_t>    samples_;
    std::unique_ptr<Codec>  codec_;
    // No destructor, copy/move constructors, or operators needed.
};

// ── Rule of Five (resource-owning classes) ───────────────────────
class SharedMemBuffer {
public:
    explicit SharedMemBuffer(std::size_t size);

    ~SharedMemBuffer();                                     // 1. destructor

    SharedMemBuffer(const SharedMemBuffer&)            = delete;  // 2. copy ctor
    SharedMemBuffer& operator=(const SharedMemBuffer&) = delete;  // 3. copy assign

    SharedMemBuffer(SharedMemBuffer&& other) noexcept;             // 4. move ctor
    SharedMemBuffer& operator=(SharedMemBuffer&& other) noexcept;  // 5. move assign

private:
    void*        ptr_  = nullptr;
    std::size_t  size_ = 0;
};
```

**Never** define only some of these — define all or none (use `= default` / `= delete`).

---

## Smart Pointers

### `std::unique_ptr` — Default Choice

```cpp
// Creation
auto codec   = std::make_unique<AacCodec>(AacCodec::Profile::kLC);
auto buffers = std::make_unique<int16_t[]>(1024);  // array form

// Transfer ownership
void processTrack(std::unique_ptr<AudioTrack> track);  // takes ownership

// Factory function (returns by unique_ptr)
std::unique_ptr<IDecoder> createDecoder(Codec codec) {
    switch (codec) {
        case Codec::kAac: return std::make_unique<AacDecoder>();
        case Codec::kMp3: return std::make_unique<Mp3Decoder>();
        default:          return nullptr;
    }
}
```

### `std::shared_ptr` — Shared Ownership

```cpp
// Use ONLY when multiple owners truly need the same lifetime
auto config = std::make_shared<AudioConfig>(sampleRate, channels);

// Inject into multiple consumers
AudioPlayer  player(config);
AudioRecorder recorder(config);  // both keep config alive

// Custom deleter (e.g. for C API handles)
auto dbus_conn = std::shared_ptr<DBusConnection>(
    dbus_bus_get(DBUS_BUS_SESSION, nullptr),
    [](DBusConnection* c) { dbus_connection_unref(c); }
);
```

### `std::weak_ptr` — Breaking Cycles

```cpp
class Widget {
    std::shared_ptr<Widget> parent_;  // WRONG — creates cycle
    std::weak_ptr<Widget>   parent_;  // CORRECT — observes without owning
public:
    void doSomethingWithParent() {
        if (auto p = parent_.lock()) {  // only valid if still alive
            p->notify();
        }
    }
};
```

### Raw Pointers — When Allowed

```cpp
// Non-owning observers only:
void adjustVolume(AudioManager* mgr, int delta);  // mgr is not owned here
void processBuffer(const int16_t* data, std::size_t len);  // read-only view
```

---

## RAII — Resource Acquisition Is Initialization

```cpp
// Every resource must be managed by an object whose destructor releases it.

// File handle
class FileHandle {
public:
    explicit FileHandle(const std::string& path)
        : fd_(::open(path.c_str(), O_RDONLY))
    {
        if (fd_ < 0) throw std::system_error(errno, std::system_category());
    }
    ~FileHandle() { if (fd_ >= 0) ::close(fd_); }

    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;
    FileHandle(FileHandle&&) = default;

    int get() const noexcept { return fd_; }
private:
    int fd_;
};

// Lock guard (already in std::)
{
    std::lock_guard<std::mutex> lock(mutex_);
    // critical section
}  // lock released here, regardless of exceptions

// Generic scope guard
template<typename F>
struct ScopeGuard {
    F fn;
    explicit ScopeGuard(F f) : fn(std::move(f)) {}
    ~ScopeGuard() { fn(); }
    ScopeGuard(const ScopeGuard&) = delete;
};
template<typename F>
auto makeScopeGuard(F f) { return ScopeGuard<F>{std::move(f)}; }

// Usage
auto guard = makeScopeGuard([&] { cleanup(); });
```

---

## Avoiding Heap Allocation in Real-Time Paths

For **QNX hard real-time** and **RTOS-like** components on Linux:

```cpp
// 1. Pre-allocate everything at startup
class RealTimeAudioProcessor {
public:
    explicit RealTimeAudioProcessor(std::size_t maxFrames)
        : buffer_(maxFrames)      // vector allocated ONCE in constructor
        , scratchpad_(maxFrames)
    {}

    // process() is called in real-time context — ZERO allocations inside
    void process(const int16_t* in, int16_t* out, std::size_t frames) noexcept {
        // Use pre-allocated buffer_/scratchpad_
    }
private:
    std::vector<int16_t> buffer_;
    std::vector<int16_t> scratchpad_;
};

// 2. Fixed-size ring buffer (no heap)
template<typename T, std::size_t N>
class RingBuffer {
    std::array<T, N> buf_{};
    std::size_t head_ = 0, tail_ = 0, count_ = 0;
public:
    bool push(T val) noexcept {
        if (count_ == N) return false;
        buf_[tail_] = std::move(val);
        tail_ = (tail_ + 1) % N;
        ++count_;
        return true;
    }
    std::optional<T> pop() noexcept {
        if (count_ == 0) return std::nullopt;
        T val = std::move(buf_[head_]);
        head_ = (head_ + 1) % N;
        --count_;
        return val;
    }
};
```

---

## AddressSanitizer (ASan) — Detecting Memory Bugs

```cmake
# CMake: enable ASan for debug/test builds
if(ENABLE_ASAN)
    target_compile_options(my_target PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer -g)
    target_link_options(my_target    PRIVATE -fsanitize=address,undefined)
endif()
```

```bash
# Run test with ASan
ASAN_OPTIONS=detect_leaks=1:check_initialization_order=1 ./build/my_test
```

ASan detects: heap/stack/global buffer overflow, use-after-free, use-after-return, double-free, memory leaks.

---

## Common Memory Bugs and Fixes

```cpp
// ── 1. Use-After-Free ────────────────────────────────────────────
{
    auto obj = std::make_unique<Foo>();
    Foo* raw = obj.get();
    obj.reset();        // object deleted
    raw->doStuff();     // UB: use-after-free — WRONG
}

// ── 2. Dangling reference ────────────────────────────────────────
std::string& getRef() {
    std::string local = "hello";
    return local;  // WRONG: returns reference to local
}

// ── 3. Double delete ─────────────────────────────────────────────
Foo* p = new Foo();
delete p;
delete p;  // UB: double delete — WRONG (use unique_ptr instead)

// ── 4. Iterator invalidation ─────────────────────────────────────
std::vector<int> v = {1, 2, 3};
for (auto it = v.begin(); it != v.end(); ++it) {
    v.push_back(*it);  // WRONG: push_back may reallocate, invalidating it
}

// ── 5. Shared ownership cycle ────────────────────────────────────
struct Node {
    std::shared_ptr<Node> next;   // WRONG for doubly-linked: creates cycle
    std::weak_ptr<Node>   prev;   // CORRECT: weak for back-links
};
```

---

## MISRA C++ Memory Rules Summary

| Rule | Requirement |
|---|---|
| M18-0-4 | Do not use dynamic heap memory after initialization |
| M5-3-3 | Expressions with side effects not used as `delete` operand |
| A18-5-2 | `operator new` / `delete` not used directly; use smart pointers |
| A18-5-8 | Objects not allocated on the heap when not necessary |

---

## Prerequisites

- GCC 9+ or Clang 12+ toolchain installed.
- CMake 3.16+ on PATH.
- For cross-compilation: ARM/AArch64 sysroot or Android NDK r25+.
- `ninja` build tool recommended for faster builds.


## Step-by-Step Workflows

### Step 1: Audit ownership
Identify each resource's lifetime; apply the Rule of Zero/Five to every class.

### Step 2: Replace raw pointers with smart pointers
Use `unique_ptr` for exclusive ownership; `shared_ptr` only when shared ownership is genuinely required.

### Step 3: Apply RAII
Wrap every resource acquisition in a constructor; release in the destructor.

### Step 4: Run AddressSanitizer
Build with `-fsanitize=address,undefined`; run all tests; fix every reported issue.

### Step 5: Review with clang-tidy
Enable `cppcoreguidelines-*` and `modernize-*` checks; fix `owning_memory` and `avoid-c-arrays` warnings.


## Troubleshooting

- **AddressSanitizer reports `heap-use-after-free`** — a raw pointer is used after its owning `unique_ptr` was destroyed; refactor to use `shared_ptr` / `weak_ptr`.
- **`shared_ptr` reference cycle causes undetected leak** — use `weak_ptr` for back-references; verify with AddressSanitizer `--detect_leaks=1`.
- **`std::bad_alloc` in production** — preallocate memory pools for real-time paths; avoid dynamic allocation in interrupt handlers.
- **RAII destructor throwing exception** — destructors must never throw; catch exceptions internally and log them.


## Pre-Commit Checklist

- [ ] No raw `new` / `delete` — use `std::make_unique` or `std::make_shared`.
- [ ] No raw owning pointers in function signatures — use smart pointer parameters.
- [ ] Every class with a user-defined destructor follows the Rule of Five (or uses `= delete` for copy).
- [ ] No `std::shared_ptr` cycles — back-pointers use `std::weak_ptr`.
- [ ] RAII used for all resources: file descriptors, locks, memory-mapped regions, D-Bus connections.
- [ ] Real-time path verified to contain zero heap allocations.
- [ ] ASan run on unit tests (no leaks reported at exit).
- [ ] No `reinterpret_cast` for pointer arithmetic — use `std::byte*` or `char*`.

---

## References

- [C++ Core Guidelines: Resource Management](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#r-resource-management)
- [Herb Sutter — GotW #89: Smart Pointers](https://herbsutter.com/2013/05/29/gotw-89-solution-smart-pointers/)
- [AddressSanitizer Docs](https://github.com/google/sanitizers/wiki/AddressSanitizer)
- [cppreference: std::unique_ptr](https://en.cppreference.com/w/cpp/memory/unique_ptr)
