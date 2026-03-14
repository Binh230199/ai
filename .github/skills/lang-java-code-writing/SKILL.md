---
name: lang-java-code-writing
description: >
  Use when writing, reviewing, or refactoring Java code (*.java) in an Android
  Automotive context (IVI, HUD, RSE on Android / AOSP). Covers Modern Java 8–17
  idioms, SOLID principles, OOP design, immutability, null safety, clean error
  handling, concurrency, design patterns, Javadoc documentation, and a full
  pre-commit review checklist. Applies to Android Framework, Android App, and
  Android System Service development.
argument-hint: <class-or-module-name> [write|review|refactor]
---

# Java Code Writing — Android Automotive

Expert-level best practices for writing production-quality Java on Android
Automotive / AOSP platforms, guided by the principles of Joshua Bloch
(Effective Java), Robert C. Martin (Clean Code), and the Android Code Style Guide.

Standards baseline: **Java 11** (default) · **Java 8** min · **Java 17** where available.

---

## When to Use This Skill

- Writing a new Java class, service, or module for Android Framework or App layers.
- Reviewing a Gerrit patch that touches `.java` files.
- Refactoring legacy Java to modern idioms (streams, optionals, records).
- Designing an Android System Service, AIDL interface, or Car API integration.
- Generating Javadoc class / method documentation.

---

## Prerequisites

- Java version confirmed: **Java 11** (default for AOSP), Java 8 min, Java 17 if available.
- Target confirmed: Android Framework (`com.android.*`), Android App, or System Service.
- Android SDK / AOSP build environment available.
- Kotlin is out of scope here — use the `kotlin-code-writing` skill.

---

## 1. Package & File Organization

> Goal: clear module boundaries; one concept per file; zero circular dependencies.

- One **top-level public class** per `.java` file; file name must match the class name exactly.
- Package names: all lowercase, reverse-domain convention — `com.company.module.feature`.
- Never use the default (unnamed) package.
- Group imports: Android / AOSP imports → third-party → `java.*` / `javax.*`. Remove unused imports — no wildcards (`import java.util.*`).
- Keep classes focused: aim for < 300 lines. If a class grows beyond that, look for extraction opportunities.
- Use package-private visibility as the default for internal implementation classes — not everything needs to be `public`.

```java
package com.automotive.sensor;

import android.content.Context;              // Android first
import android.util.Log;

import com.automotive.hal.IAdcDriver;        // project

import java.util.Optional;                  // java.* last
```

---

## 2. Class Design & SOLID Principles

> Goal: classes that are easy to understand, test, extend, and replace independently.

### Single Responsibility (S)
- Each class has **one reason to change** — one job, one actor that owns it.
- Activity / Fragment: only UI logic. ViewModel: only presentation state. Repository: only data access. Never mix concerns.
- If the class name contains "And", "Manager", or "Helper" spanning multiple domains, split it.

### Open / Closed (O)
- Extend behaviour via **new implementations or injected strategies**, not by modifying existing classes.
- Use interfaces and abstract classes as stable extension points — callers depend on the abstraction.

### Liskov Substitution (L)
- A subclass must honour **every contract** of its superclass: don't throw unchecked exceptions the parent doesn't throw, don't weaken preconditions.
- If overriding breaks callers, prefer composition (`has-a`) over inheritance.

### Interface Segregation (I)
- Prefer **narrow, role-specific interfaces** over fat interfaces.
- A class implementing an interface should use every method it provides.

```java
// GOOD — focused interfaces
interface Readable  { float read(); }
interface Writable  { void  write(float value); }

// BAD — forces all implementors to provide unused methods
interface SensorGod { float read(); void write(float v); void calibrate(); void reset(); }
```

### Dependency Inversion (D)
- High-level classes must not depend on concrete low-level classes — both depend on **interfaces**.
- Inject dependencies through the **constructor** — never instantiate concrete collaborators inside a class.
- In Android: use constructor injection (Hilt / Dagger) or manual injection in tests.

```java
// GOOD — ThermalMonitor depends on the ISensor interface, not a concrete class
public final class ThermalMonitor {
    private final ISensor mSensor;

    public ThermalMonitor(@NonNull ISensor sensor) {
        mSensor = Objects.requireNonNull(sensor, "sensor must not be null");
    }
}
```

---

## 3. Immutability & Object Design

> Prefer immutable objects. Mutability is the root cause of most concurrency bugs.

- Declare fields `final` whenever possible — signals intent clearly and enables safe sharing.
- Make classes `final` unless designed for inheritance. Document inheritance contracts explicitly with `@NonNull`/`@Nullable` and override invariants.
- Prefer **value objects** (immutable data carriers) over mutable beans.
- Builder pattern for objects with ≥ 3 optional parameters — avoid telescoping constructors.
- Override `equals()`, `hashCode()`, and `toString()` for value objects — always together, never partially.
- Use Java 16+ **records** (`record Point(int x, int y) {}`) for pure data carriers when the toolchain allows.

```java
// GOOD — immutable value object
public final class Temperature {
    private final float mDegC;

    public Temperature(float degC) {
        mDegC = degC;
    }

    public float getDegC() { return mDegC; }

    @Override public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Temperature)) return false;
        return Float.compare(((Temperature) o).mDegC, mDegC) == 0;
    }

    @Override public int hashCode() { return Float.hashCode(mDegC); }

    @Override public String toString() { return "Temperature{" + mDegC + "°C}"; }
}
```

---

## 4. Null Safety

> Every `NullPointerException` in production is a design failure.

- Annotate all method parameters, return types, and fields with `@NonNull` or `@Nullable` (androidx annotation or `javax.annotation`). Be explicit — unannotated means unknown.
- Validate `@NonNull` parameters at the **top of every constructor and public method**:
  `Objects.requireNonNull(param, "param must not be null");`
- Prefer `Optional<T>` as a **return type** when a method may legitimately return no value — never return `null` from a public API.
- Never pass `null` intentionally — redesign the API or use `Optional`/overloading.
- Use `@Nullable` + explicit null-check over silent null-swallowing patterns like `if (x != null)` scattered throughout business logic.

```java
// GOOD — Optional as explicit "no value" return
public Optional<Float> tryReadDegC() {
    if (!mIsInitialised) { return Optional.empty(); }
    return Optional.of(convertAdcToTemp(mDriver.readChannel(mChannel)));
}

// BAD — null return forces every caller to guess whether null is possible
public Float readDegC() {
    if (!mIsInitialised) { return null; }   // callers won't know to check
    return convertAdcToTemp(mDriver.readChannel(mChannel));
}
```

---

## 5. Modern Java Idioms (Java 8–17)

> Prefer language features that remove boilerplate and eliminate bug classes.

- **`var` (Java 10)** — use for local variables when the type is obvious from the right-hand side. Avoid when it obscures type intent.
- **Lambdas & method references** — replace single-method anonymous classes. Prefer method references (`ClassName::method`) over equivalent lambdas.
- **Streams** — use for declarative data transformation pipelines. Avoid side effects inside `map`/`filter`. Prefer `collect(Collectors.toUnmodifiableList())` over mutable lists.
- **`Optional<T>`** — return type for "maybe a value". Never wrap `Optional` in another `Optional` or use it as a field/parameter type.
- **`switch` expressions (Java 14)** — prefer over `switch` statements; exhaustive, returns a value.
- **Records (Java 16)** — concise immutable data carriers replacing boilerplate POJOs.
- **`instanceof` pattern matching (Java 16)** — `if (obj instanceof String s)` eliminates explicit cast.
- **Sealed classes (Java 17)** — constrain inheritance to a known set of subtypes.
- **`Collections.unmodifiableList` / `List.of` / `Map.of`** — return unmodifiable views from getters; never expose mutable internal collections.

```java
// Method reference over lambda
list.stream()
    .filter(Objects::nonNull)
    .map(String::toUpperCase)
    .collect(Collectors.toUnmodifiableList());

// switch expression (Java 14)
String label = switch (state) {
    case IDLE    -> "Idle";
    case ACTIVE  -> "Active";
    case FAULT   -> "Fault";
};

// instanceof pattern matching (Java 16)
if (event instanceof TemperatureEvent te) {
    process(te.getDegC());
}
```

---

## 6. Error Handling

> Choose one strategy per module boundary. Never swallow exceptions silently.

| Context | Strategy | Rationale |
|---|---|---|
| Programming errors (preconditions) | `throw new IllegalArgumentException` / `IllegalStateException` | Fail fast; not recoverable by caller |
| Recoverable failures in business logic | **Checked exceptions** or `Optional<T>` / result type | Forces callers to handle explicitly |
| I/O, system, hardware failures | **Checked exceptions** (`IOException`, custom domain exception) | Explicit error propagation |
| Android callbacks / async paths | **Error callback / `LiveData<Result<T>>`** | Exception can't propagate across thread boundary cleanly |

- Never `catch (Exception e) { /* swallow */ }` — at minimum log and rethrow or propagate.
- Never use exceptions for control flow (e.g., catching `NumberFormatException` instead of calling `isDigit`).
- Create **domain-specific exception types** for different failure categories — `SensorException`, `HalException`.
- Always log at the point of first catch with full context (`Log.e(TAG, "readTemp failed: channel=" + mChannel, e)`).
- In Android: avoid throwing exceptions across Binder calls — use `ServiceSpecificException` or return status codes via AIDL.

```java
// GOOD — domain exception with context
public float readDegC() throws SensorException {
    if (!mIsInitialised) {
        throw new IllegalStateException("TemperatureSensor not initialised");
    }
    try {
        return mDriver.readChannel(mChannel);
    } catch (HalException e) {
        throw new SensorException("Failed to read ADC channel " + mChannel, e);
    }
}
```

---

## 7. Concurrency & Thread Safety

> Android has a strict main-thread rule. Design for it from the start.

- Document the thread-safety contract of every class and method with `@MainThread`, `@WorkerThread`, `@AnyThread`, `@GuardedBy("mLock")` annotations (androidx).
- **Never** do I/O, blocking calls, or long computation on the **main/UI thread** — use `ExecutorService`, `HandlerThread`, or coroutines.
- Protect shared mutable state with `synchronized` blocks or `java.util.concurrent.locks.ReentrantLock`. Prefer the latter for tryLock / fairness needs.
- Use `java.util.concurrent` atomic types (`AtomicBoolean`, `AtomicInteger`) for simple shared flags — cheaper than `synchronized`.
- Prefer **immutable data + message passing** over shared mutable state. In Android: use `Handler` / `Looper` for thread-confined state, `LiveData` / `Flow` for observable state across threads.
- Use `volatile` only for single-variable visibility guarantees — it is **not** a substitute for synchronisation of compound actions.
- Use `ConcurrentHashMap`, `CopyOnWriteArrayList` for shared collections instead of manual synchronization.
- Use `CountDownLatch`, `Semaphore`, `BlockingQueue` from `java.util.concurrent` for cross-thread coordination — not `wait`/`notify` directly.

```java
@GuardedBy("mLock")
private float mLatestDegC;
private final Object mLock = new Object();

/** @thread_safety Safe for concurrent readers and a single writer. */
@AnyThread
public float getLatestDegC() {
    synchronized (mLock) { return mLatestDegC; }
}

@WorkerThread
public void update(float degC) {
    synchronized (mLock) { mLatestDegC = degC; }
}
```

---

## 8. Design Patterns

> Pick the simplest pattern that solves the problem. Over-engineering is a defect.

### Creational

| Pattern | When to use | Java idiom |
|---|---|---|
| **Factory Method** | Decouple creation from use; subclasses decide the concrete type | Static `create()` / `newInstance()` returning interface type |
| **Abstract Factory** | Families of platform-specific objects (sensor suite per SoC vendor) | Interface with multiple `make*()` factory methods |
| **Builder** | Object with ≥ 3 optional / validated parameters | Inner static `Builder` class; `build()` validates and returns the product |
| **Singleton** | Process-wide resource (logger, config). Prefer DI; use sparingly | `enum` singleton or `private static final` instance + `getInstance()` |

### Structural

| Pattern | When to use | Java idiom |
|---|---|---|
| **Adapter** | Wrap an incompatible legacy or C HAL API behind a Java interface | Class implementing `IFoo`, delegating to legacy handle |
| **Facade** | Single clean entry point to a complex subsystem (e.g., `CarSensorManager`) | One class delegating internally; hides subsystem classes |
| **Decorator** | Add cross-cutting behaviours (logging, retry, caching) without subclassing | Implements same interface, wraps delegate, augments calls |
| **Proxy** | Lazy init, access control, remoting (Binder stub is a proxy) | Implements same interface, intercepts calls |

### Behavioural

| Pattern | When to use | Java idiom |
|---|---|---|
| **Strategy** | Swap algorithm at runtime without touching the host class | Interface injected via constructor; `@FunctionalInterface` for single-method |
| **Observer** | Decouple an event source from N listeners (event bus, LiveData) | `interface Listener { void onEvent(E e); }` + `addListener` / `removeListener` |
| **State** | Object's behaviour changes entirely based on internal state | Enum states + switch, or `IState` interface with polymorphic dispatch |
| **Command** | Encapsulate an operation (queue, undo, delayed execution) | `Runnable` / `Callable` / `@FunctionalInterface Command` |
| **Template Method** | Fixed algorithm skeleton; steps customised by subclass | Abstract class with `final` public method + `protected abstract` hook methods |

```java
// Builder — avoids telescoping constructors
public final class SensorConfig {
    private final int    mChannel;
    private final long   mTimeoutMs;
    private final String mTag;

    private SensorConfig(Builder b) {
        mChannel   = b.mChannel;
        mTimeoutMs = b.mTimeoutMs;
        mTag       = b.mTag;
    }

    public static final class Builder {
        private int    mChannel;
        private long   mTimeoutMs = 100L;
        private String mTag = "Sensor";

        public Builder channel(int channel)      { mChannel = channel; return this; }
        public Builder timeoutMs(long ms)        { mTimeoutMs = ms;   return this; }
        public Builder tag(@NonNull String tag)  { mTag = tag;        return this; }
        public SensorConfig build()              { return new SensorConfig(this); }
    }
}

// Strategy via @FunctionalInterface
@FunctionalInterface
public interface SensorFilter { float apply(float raw); }

SensorFilter lowPass = raw -> raw * 0.9f + mPrev * 0.1f;
```

---

## 9. Android-Specific Best Practices

> Android has its own lifecycle, IPC model, and resource constraints on top of Java.

- **Context leaks**: never store `Activity` context in a `static` field or in a long-lived object. Use `Application` context for non-UI resources.
- **`WeakReference`** for callbacks and listeners that might outlive the component. Always unregister in `onDestroy` / `onStop`.
- **Binder / AIDL**: methods called on the Binder thread, not the main thread. Never assume otherwise. Use `@NonNull`/`@Nullable` in `.aidl` files.
- **Lifecycle-awareness**: prefer `LifecycleObserver` / `DefaultLifecycleObserver` over manual `onStart`/`onStop` bookkeeping.
- **Resources**: release `Cursor`, `ParcelFileDescriptor`, `MediaPlayer`, and similar in `finally` or `try-with-resources`.
- **Permissions**: check at runtime before use — never assume a permission is still granted after the initial check.
- **`Log` tag**: `private static final String TAG = TemperatureSensor.class.getSimpleName();` — max 23 chars (Android limit).
- **`Handler` / `HandlerThread`**: always call `quit()` or `quitSafely()` when the component is destroyed to prevent leaks.

```java
// try-with-resources for Android resources
try (Cursor cursor = db.query(table, columns, null, null, null, null, null)) {
    while (cursor.moveToNext()) {
        processRow(cursor);
    }
}

// Lifecycle-aware component
public class SensorObserver implements DefaultLifecycleObserver {
    @Override public void onStart(@NonNull LifecycleOwner owner)  { register(); }
    @Override public void onStop(@NonNull LifecycleOwner owner)   { unregister(); }
}
```

---

## 10. Documentation (Javadoc)

> If the intent is not obvious from the code alone, document it before writing the code.

- Every public class needs a `/** @brief summary */` block stating its purpose and context.
- Every public method: summary sentence, `@param`, `@return`, `@throws` for each checked and commonly thrown unchecked exception.
- `@NonNull` / `@Nullable` on every parameter and return type — treat it as part of the API contract.
- `@GuardedBy`, `@MainThread`, `@WorkerThread`, `@AnyThread` on methods and fields with threading constraints.
- `@hide` in AOSP/framework code to exclude from public SDK Javadoc while keeping internal docs.
- `{@link ClassName#method}` to cross-reference related APIs.

```java
/**
 * Reads the current temperature from the NTC thermistor on the configured ADC channel.
 *
 * @return Temperature in degrees Celsius, or {@link Optional#empty()} on hardware error.
 *
 * @throws IllegalStateException if {@link #init()} has not been called successfully.
 * @thread_safety Safe for concurrent callers after successful {@link #init()}.
 */
@WorkerThread
@NonNull
public Optional<Float> readDegC() { /* … */ }
```

---

## Step-by-Step Workflows

### Step 1: Set up the file structure
Use the correct package declaration; name the file after the public class.

### Step 2: Design the class
Apply immutability where possible; annotate with `@NonNull` / `@Nullable` consistently.

### Step 3: Apply the patterns from this skill
Follow sections 1–10 below in order: naming → null safety → modern Java → error handling, etc.

### Step 4: Run Android Lint
Fix all **Error** severity issues; investigate and address **Warning** issues.

### Step 5: Write unit tests
Use JUnit 4/5 with Mockito; test every public method with at least a happy-path test.


## Pre-Commit Review Checklist

Before pushing to Gerrit, verify:

**Package & file**
- [ ] One top-level public class per `.java` file; file name matches class name
- [ ] Package name is lowercase, reverse-domain; no default package
- [ ] No wildcard imports; no unused imports

**Class design**
- [ ] Each class has a single, clearly stated responsibility
- [ ] Constructors validate `@NonNull` parameters with `Objects.requireNonNull`
- [ ] Immutable fields declared `final`; value objects override `equals`/`hashCode`/`toString`

**Null safety**
- [ ] All public parameters and return types annotated `@NonNull` or `@Nullable`
- [ ] No public method returns `null` — use `Optional<T>` or throw
- [ ] No silent null-swallowing; null checks have explicit consequences

**Modern Java**
- [ ] No anonymous inner classes where a lambda / method reference suffices
- [ ] `List.of` / `Map.of` / `Collections.unmodifiableList` for collections returned from getters
- [ ] `Optional<T>` used as return type, not as parameter or field type

**Error handling**
- [ ] No empty `catch` blocks — at minimum log + rethrow
- [ ] Exceptions carry full context (message + cause)
- [ ] No exceptions across Binder calls — use `ServiceSpecificException` or status codes

**Concurrency**
- [ ] Thread-safety contract documented (`@MainThread`, `@WorkerThread`, `@GuardedBy`)
- [ ] No I/O or blocking calls on the main thread
- [ ] Shared mutable state protected by `synchronized` or `java.util.concurrent`

**Android-specific**
- [ ] No `Activity` context stored in static fields or long-lived objects
- [ ] All `Cursor` / `ParcelFileDescriptor` / closeable resources in `try-with-resources`
- [ ] Listeners / callbacks unregistered in the matching lifecycle callback

**Documentation**
- [ ] Every public class has a Javadoc summary
- [ ] Every public method has `@param`, `@return`, `@throws`

---

## Examples

See companion files:
- [GoodTemperatureSensor.java](./examples/GoodTemperatureSensor.java) — SOLID, null-safe, Javadoc, Optional return
- [BadSensor.java](./examples/BadSensor.java) — common anti-patterns annotated line by line

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `NullPointerException` in production | Missing null check on input or return value | Add `@NonNull`/`@Nullable` and `requireNonNull` guards |
| `NetworkOnMainThreadException` | Blocking I/O on UI thread | Move to `ExecutorService` or `WorkerThread` |
| `ConcurrentModificationException` | Iterating while modifying collection | Copy-on-iterate or use `ConcurrentHashMap` |
| Binder exception: `DeadObjectException` | Service crashed; client still calling | Catch `RemoteException`, reconnect via `ServiceConnection` |
| Memory leak in Activity | Static reference to Activity context | Use `WeakReference` or `ApplicationContext`; unregister listeners |
| `IllegalStateException: Fragment not attached` | Callback fires after `onDetach` | Guard fragment callbacks with `isAdded()` check |

---

## References

- [Effective Java (3rd Ed.)](https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/) — Joshua Bloch
- [Android Code Style Guide](https://source.android.com/docs/setup/contribute/code-style)
- [Android Architecture Guide](https://developer.android.com/topic/architecture)
- [Java Concurrency in Practice](https://jcip.net/) — Goetz et al.
- Internal skill: [kotlin-code-writing](../kotlin-code-writing/SKILL.md) — Kotlin equivalent for the same platforms
