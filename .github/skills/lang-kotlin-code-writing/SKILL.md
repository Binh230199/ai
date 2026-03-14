---
name: lang-kotlin-code-writing
description: >
  Use when writing, reviewing, or refactoring Kotlin code (*.kt) for Android
  App development (IVI, HUD, RSE on Android Automotive / AOSP).
  Covers Kotlin idioms, null safety, coroutines, Flow, MVVM/MVI architecture,
  Jetpack Compose, immutability, extension functions, design patterns, KDoc
  documentation, and a full pre-commit review checklist.
  Focused on the App layer — not Android Framework / System Services.
argument-hint: <class-or-module-name> [write|review|refactor]
---

# Kotlin Code Writing — Android App

Expert-level best practices for writing production-quality Kotlin Android Apps
on Android Automotive / AOSP platforms, guided by Kotlin's official style guide,
Android Architecture Guide, and Clean Architecture principles.

Standards baseline: **Kotlin 1.9** (default) · **Kotlin 1.5** min · **Coroutines**, **Flow**, **Jetpack**.

---

## When to Use This Skill

- Writing a new Kotlin class, ViewModel, Repository, or composable from scratch.
- Reviewing a Gerrit / GitHub PR that touches `.kt` files in an Android App module.
- Refactoring Java-style Kotlin to idiomatic Kotlin.
- Designing coroutine / Flow pipelines, MVVM state management, or Compose UI.
- Generating KDoc class / function documentation.

---

## Prerequisites

- Kotlin version confirmed: **1.9** (default), 1.5 min.
- Android project confirmed (Gradle with `kotlin-android` plugin).
- Coroutines + Flow available (`org.jetbrains.kotlinx:kotlinx-coroutines-android`).
- Jetpack (ViewModel, LiveData or StateFlow, Navigation, Compose) available.
- Android Framework / System Services are out of scope — use `java-code-writing` for those.

---

## 1. File & Package Organization

> Goal: one concept per file, clear module boundaries, zero circular dependencies.

- File name = top-level class / object name. For top-level functions and extensions, use a descriptive name: `SensorExtensions.kt`, `DateFormatters.kt`.
- Package names: all lowercase, reverse-domain — `com.company.feature.ui`.
- One top-level `class` / `object` / `interface` per file. Multiple closely related small classes or top-level functions in the same file is acceptable — use judgement.
- Group imports: Android / Jetpack → third-party → `kotlin.*` / `java.*`. Remove unused imports.
- Keep files focused: aim for < 300 lines. Extract delegates, extensions, or helper objects when a file grows beyond that.
- Put **extension functions** for a type in a dedicated file: `ContextExtensions.kt`, never scattered across unrelated files.

```kotlin
package com.automotive.sensor.ui

import androidx.lifecycle.ViewModel              // Android / Jetpack
import androidx.lifecycle.viewModelScope

import dagger.hilt.android.lifecycle.HiltViewModel  // third-party

import kotlinx.coroutines.flow.StateFlow         // kotlin.*
import kotlinx.coroutines.launch

import java.util.Locale                          // java.*
```

---

## 2. Kotlin Null Safety

> Kotlin's type system eliminates null at compile time — use it fully. `!!` is a code smell.

- Prefer **non-nullable types** as the default. Add `?` only when null is a genuine valid state for the domain.
- Never use `!!` (`null-assertion`) in production code — it converts a compile-time guarantee into a runtime crash. Use safe-call `?.`, Elvis `?:`, `requireNotNull`, or `checkNotNull` instead.
- Use the **Elvis operator** `?:` to provide a default or throw with context:
  `val name = input ?: throw IllegalArgumentException("name must not be null")`.
- `let`, `run`, `also`, `apply` scope functions for null-safe access chains — choose the right one:

| Scope fn | Receiver | Returns | Best for |
|---|---|---|---|
| `let` | `it` | lambda result | Null check + transform: `value?.let { transform(it) }` |
| `run` | `this` | lambda result | Object config + compute result |
| `apply` | `this` | receiver | Object initialisation / builder-style config |
| `also` | `it` | receiver | Side effects (logging) without breaking the chain |
| `with` | `this` | lambda result | Multiple calls on the same non-null object |

- Use `lateinit var` only for DI-injected fields guaranteed non-null after `onCreate` / `inject`. Always prefer `val` + initialiser.
- Use `by lazy { }` for expensive one-time initialisations — thread-safe by default.

```kotlin
// GOOD — safe, expressive
val tempLabel = sensor.readDegC()?.let { "%.1f °C".format(it) } ?: "N/A"

// BAD — runtime crash if null
val tempLabel = sensor.readDegC()!!.toString()
```

---

## 3. Immutability & Data Modelling

> Immutable state is easier to reason about, test, and share across threads.

- Prefer `val` over `var` everywhere. Use `var` only when mutation is genuinely required (e.g., loop accumulator, mutable ViewModel state backing property).
- Use **`data class`** for value objects (UI state, domain models, DTOs). They give `equals`, `hashCode`, `toString`, and `copy` for free.
- Use **`sealed class` / `sealed interface`** to model exhaustive domain states — the compiler enforces handling every branch in `when`.
- Use **`object`** for singletons and companion-object factories; not for stateful global mutable state.
- Use **`enum class`** for a fixed set of named constants with no additional state. Prefer `sealed class` when variants carry data.
- Use **`value class` (inline class)** to wrap primitives with domain semantics at zero runtime cost.
- Expose state as `val` with a private `var` backing property (ViewModels):

```kotlin
// GOOD — immutable UI state modelled with sealed interface
sealed interface SensorUiState {
    object Loading : SensorUiState
    data class Success(val tempDegC: Float) : SensorUiState
    data class Error(val message: String)   : SensorUiState
}

// GOOD — private mutable + public immutable StateFlow
private val _uiState = MutableStateFlow<SensorUiState>(SensorUiState.Loading)
val uiState: StateFlow<SensorUiState> = _uiState.asStateFlow()
```

---

## 4. Functions & Kotlin Idioms

> Prefer expressive, concise Kotlin over verbose Java-style patterns.

- **Single-expression functions** — use `=` body for functions that return a single expression.
- **Named arguments** — use when a function has ≥ 2 parameters of the same type, or when meaning is not obvious from position.
- **Default parameters** — eliminate overload proliferation. One function with defaults beats 3 overloads.
- **Destructuring** — `val (x, y) = point` for `data class`; `for ((key, value) in map)`.
- **`when` expressions** — prefer over `if-else if` chains; use as expression (returns a value). Always add `else` unless `when` is over a `sealed` type (exhaustive).
- **Trailing lambdas** — move the last lambda argument outside parentheses: `list.filter { it > 0 }`.
- **`apply` / `also`** for fluent object construction — replaces builder boilerplate for simple cases.
- **`require` / `check` / `error`** for precondition validation — throw `IllegalArgumentException` / `IllegalStateException` with a message.
- **`@JvmStatic` / `@JvmOverloads`** only when Java interop requires it — do not add them blindly.
- **`typealias`** to give meaningful names to function types or complex generics.

```kotlin
// Single-expression function
fun Float.toTempLabel(): String = "%.1f °C".format(this)

// Default parameters — no overloads needed
fun schedulePoll(channelId: Int, intervalMs: Long = 1_000L, retries: Int = 3) { … }

// Named arguments for clarity
schedulePoll(channelId = 2, retries = 5)

// when as exhaustive expression over sealed type
val message = when (val state = uiState.value) {
    is SensorUiState.Loading        -> "Loading…"
    is SensorUiState.Success        -> state.tempDegC.toTempLabel()
    is SensorUiState.Error          -> "Error: ${state.message}"
}

// require / check
fun readChannel(channel: Int): Float {
    require(channel in 0..7) { "channel must be 0–7, got $channel" }
    check(mIsInitialised) { "Sensor not initialised" }
    return mDriver.read(channel)
}
```

---

## 5. Coroutines & Structured Concurrency

> Coroutines replace threads and callbacks. Structured concurrency prevents leaks.

- **Never** use `GlobalScope` — always use a structured scope (`viewModelScope`, `lifecycleScope`, or a custom `CoroutineScope` tied to a component lifecycle).
- Use the correct **dispatcher**:

| Dispatcher | Use |
|---|---|
| `Dispatchers.Main` | UI updates, LiveData / StateFlow emissions |
| `Dispatchers.IO` | File I/O, network, database (suspends, many threads) |
| `Dispatchers.Default` | CPU-intensive work (parsing, sorting, crypto) |
| `Dispatchers.Main.immediate` | Already on main thread; skip re-dispatch overhead |

- Inject dispatchers — never hardcode `Dispatchers.IO` in production classes. Pass a `CoroutineDispatcher` parameter defaulting to `Dispatchers.IO` so tests can inject `StandardTestDispatcher`.
- `suspend` functions should be **main-safe**: switch to the right dispatcher internally with `withContext`. Callers should not need to worry about which thread to call from.
- Use `supervisorScope` when child coroutine failures should not cancel siblings.
- Handle exceptions: `CoroutineExceptionHandler` for top-level `launch`; `try/catch` inside `async` / `suspend` functions.
- Cancel gracefully: always check `isActive` in long loops; prefer `ensureActive()`.

```kotlin
// GOOD — main-safe suspend function, injected dispatcher
class SensorRepository(
    private val driver: IAdcDriver,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO
) {
    suspend fun readDegC(channel: Int): Result<Float> = withContext(ioDispatcher) {
        runCatching { driver.readChannel(channel) }
    }
}

// GOOD — ViewModel launches in structured scope
@HiltViewModel
class SensorViewModel @Inject constructor(
    private val repo: SensorRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<SensorUiState>(SensorUiState.Loading)
    val uiState: StateFlow<SensorUiState> = _uiState.asStateFlow()

    fun load(channel: Int) {
        viewModelScope.launch {
            _uiState.value = SensorUiState.Loading
            repo.readDegC(channel)
                .onSuccess { _uiState.value = SensorUiState.Success(it) }
                .onFailure { _uiState.value = SensorUiState.Error(it.message ?: "Unknown") }
        }
    }
}
```

---

## 6. Flow

> `Flow` replaces `LiveData` for reactive streams in Kotlin-first codebases.

- Prefer **`StateFlow`** for UI state (single current value, always has value, hot).
- Prefer **`SharedFlow`** for events that should not be replayed (navigation, one-shot toasts).
- Use **`callbackFlow`** or **`flow { }`** to wrap callback-based APIs as cold flows.
- **Never** collect a Flow inside another `flow { }` builder — compose with operators (`map`, `flatMapLatest`, `combine`, `zip`).
- Collect in the UI layer with `repeatOnLifecycle(Lifecycle.State.STARTED)` — not `lifecycleScope.launch` directly (which keeps collecting in the background).
- Use `stateIn(scope, SharingStarted.WhileSubscribed(5_000), initial)` to convert cold flows to hot `StateFlow` in ViewModel.
- Use `flowOn(dispatcher)` at the **source** to switch context; do not use `withContext` inside a `flow { }` builder.
- Backpressure: use `buffer()`, `conflate()`, or `collectLatest` to handle fast producers.

```kotlin
// Repository — cold flow from hardware polling
fun temperatureStream(channel: Int): Flow<Float> = flow {
    while (true) {
        emit(driver.readChannel(channel))
        delay(1_000L)
    }
}.flowOn(ioDispatcher)    // upstream runs on IO; collector stays on its own context

// ViewModel — convert to StateFlow
val temperature: StateFlow<Float> = repo.temperatureStream(channel = 3)
    .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000L), initialValue = 0f)

// UI — collect safely
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.temperature.collect { temp -> updateUi(temp) }
    }
}
```

---

## 7. MVVM Architecture & Clean Layers

> Separate concerns strictly — each layer has one job and one direction of dependency.

```
UI (Compose / View)
    ↓ observes
ViewModel  (state holder; survives config changes)
    ↓ calls
Repository (single source of truth; abstracts data sources)
    ↓ uses
DataSource / DAO / Remote API / HAL
```

Rules:
- **UI** knows only ViewModel. Never calls Repository or DataSource directly.
- **ViewModel** knows only Repository interfaces. Never imports `android.view.*` or `android.widget.*`.
- **Repository** owns data-source selection logic (cache vs. network vs. HAL). Exposes `suspend` functions or `Flow`.
- **DataSource** wraps a single origin (Room DAO, Retrofit service, Binder HAL call). No business logic.
- Domain models (data classes) live in a shared `domain` package — no Android imports.
- Use **`Result<T>`** or a sealed `DomainResult` type to propagate success/error across layer boundaries — not raw exceptions.
- All Repository / DataSource methods are `suspend` or return `Flow` — never blocking.

```kotlin
// Repository interface — testable, platform-agnostic
interface SensorRepository {
    suspend fun readDegC(channel: Int): Result<Float>
    fun temperatureStream(channel: Int): Flow<Float>
}

// ViewModel only knows the interface
@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val sensorRepo: SensorRepository   // interface, not impl
) : ViewModel() { … }
```

---

## 8. Dependency Injection (Hilt)

> DI removes manual wiring, enables testing, and enforces layer boundaries.

- Annotate every ViewModel with `@HiltViewModel` + `@Inject constructor(...)`.
- Provide dependencies in `@Module` + `@InstallIn` classes, not in `Application.onCreate`.
- Bind interfaces to implementations with `@Binds` in abstract modules — not `@Provides` (cleaner, no unnecessary instantiation).
- Use scopes correctly: `@Singleton` (app lifetime), `@ViewModelScoped` (ViewModel lifetime), `@ActivityScoped` (Activity lifetime). Never use `@Singleton` for something that holds UI state.
- Do **not** pass `Context` down to Repository or lower — inject `@ApplicationContext Context` at the module level.
- For coroutine dispatchers: define a `@Qualifier` (`@IoDispatcher`, `@DefaultDispatcher`) and bind in a module. Inject the qualifier, not the raw `Dispatchers` object.

```kotlin
// Module binding interface to impl
@Module
@InstallIn(SingletonComponent::class)
abstract class SensorModule {

    @Binds
    @Singleton
    abstract fun bindSensorRepository(
        impl: SensorRepositoryImpl
    ): SensorRepository
}

// Dispatcher qualifier
@Qualifier @Retention(AnnotationRetention.BINARY)
annotation class IoDispatcher

@Module @InstallIn(SingletonComponent::class)
object DispatchersModule {
    @Provides @IoDispatcher
    fun provideIoDispatcher(): CoroutineDispatcher = Dispatchers.IO
}
```

---

## 9. Jetpack Compose

> Compose replaces XML layouts. Composables are pure functions of state.

- **Composables are stateless by default** — state lives in ViewModel, not inside composables (except for ephemeral UI state like `TextField` text before submission).
- Hoist state up to the lowest common ancestor that needs it. Pass state and callbacks (lambdas) down — never pass ViewModel references into deep composables.
- Annotate composables with `@Composable`. Preview with `@Preview`.
- Name composables as **nouns or noun-phrases** in PascalCase: `TemperatureCard`, `SensorDashboard`. Not verbs.
- **Side effects** only inside `LaunchedEffect`, `DisposableEffect`, `SideEffect` — never directly in the composable body.
- Use `remember` to survive recompositions; `rememberSaveable` to survive process death.
- Avoid unnecessary recompositions: pass only the data a composable needs, not the entire state object. Use `derivedStateOf` for computed values.
- Extract reusable composables into their own files. Keep each composable ≤ 50 lines; extract sub-composables when it grows.

```kotlin
// GOOD — stateless composable, state and callbacks from above
@Composable
fun TemperatureCard(
    tempDegC: Float,
    onRefreshClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier) {
        Column(Modifier.padding(16.dp)) {
            Text(text = "%.1f °C".format(tempDegC), style = MaterialTheme.typography.headlineMedium)
            Button(onClick = onRefreshClick) { Text("Refresh") }
        }
    }
}

// GOOD — screen composable connects ViewModel to stateless UI
@Composable
fun SensorScreen(viewModel: SensorViewModel = hiltViewModel()) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    when (state) {
        is SensorUiState.Loading -> CircularProgressIndicator()
        is SensorUiState.Success -> TemperatureCard(
            tempDegC = (state as SensorUiState.Success).tempDegC,
            onRefreshClick = viewModel::refresh
        )
        is SensorUiState.Error   -> ErrorView(message = (state as SensorUiState.Error).message)
    }
}
```

---

## 10. Documentation (KDoc)

> If the intent is not obvious from the code alone, document it before writing the code.

- Every public class / interface needs a KDoc summary block (`/** … */`).
- Every public function: summary line, `@param` for non-obvious parameters, `@return`, `@throws` for exceptions that can propagate.
- Extension functions: document **what type they extend and what they add** — the receiver type is often not obvious from a call site.
- Coroutines: note `@Throws` if the suspend function can throw; note which dispatcher it expects to be called from if it is **not** main-safe.
- Use `[ClassName]` / `[ClassName.functionName]` for cross-references.

```kotlin
/**
 * Reads the current temperature from the NTC thermistor.
 *
 * This function is main-safe — it switches to [IoDispatcher] internally.
 *
 * @param channel ADC channel index in range 0–7.
 * @return [Result.success] with temperature in °C, or [Result.failure] on hardware error.
 * @throws IllegalArgumentException if [channel] is outside 0–7.
 */
suspend fun readDegC(channel: Int): Result<Float>
```

---

## Step-by-Step Workflows

### Step 1: Set up the file structure
Use the correct package; prefer one top-level class per file (except for extension functions).

### Step 2: Design with Kotlin idioms
Prefer `data class` for state; use `sealed class` for result types; eliminate the `!!` operator.

### Step 3: Apply the patterns from this skill
Follow sections 1–10 below in order: null safety → coroutines → MVVM → Compose, etc.

### Step 4: Run Detekt and Android Lint
Fix all errors; add documented `@Suppress` annotations only when strictly necessary.

### Step 5: Write unit tests
Use MockK + `runTest {}` for coroutine tests; Turbine for Flow/StateFlow assertions.


## Pre-Commit Review Checklist

Before pushing to Gerrit / GitHub, verify:

**Package & file**
- [ ] File name matches top-level class / object name
- [ ] Package name is lowercase + reverse-domain
- [ ] No unused imports; no wildcard imports

**Null safety**
- [ ] No `!!` operator in production code
- [ ] `lateinit var` used only for DI fields; prefer `val` + `by lazy`
- [ ] All public API functions / properties have explicit nullability

**Immutability & modelling**
- [ ] `val` preferred over `var`; `var` justified by comment
- [ ] `data class` for value objects; `sealed class`/`interface` for domain states
- [ ] `MutableStateFlow` / `MutableSharedFlow` private; public surface is read-only

**Coroutines & Flow**
- [ ] No `GlobalScope` usage
- [ ] Dispatchers injected (not hardcoded)
- [ ] Suspend functions are main-safe (use `withContext` internally)
- [ ] Flow collected with `repeatOnLifecycle` in UI layer
- [ ] `StateFlow` created with `stateIn` in ViewModel

**Architecture**
- [ ] ViewModel imports no `android.view.*` or `android.widget.*`
- [ ] Repository depends only on DataSource interfaces
- [ ] No business logic in UI layer (Composable / Fragment / Activity)

**Hilt / DI**
- [ ] Interfaces bound with `@Binds`, not `@Provides` where possible
- [ ] Correct scope applied (`@Singleton` / `@ViewModelScoped`)
- [ ] No `Context` passed below the Repository layer

**Compose** (if applicable)
- [ ] Composables are stateless; state hoisted to ViewModel
- [ ] Side effects inside `LaunchedEffect` / `DisposableEffect`
- [ ] `modifier` parameter accepted and forwarded

**Documentation**
- [ ] Every public class has a KDoc summary
- [ ] Every public suspend function documents dispatcher requirements and `@throws`

---

## Examples

See companion files:
- [GoodSensorViewModel.kt](./examples/GoodSensorViewModel.kt) — MVVM, StateFlow, Hilt, coroutines
- [GoodSensorRepository.kt](./examples/GoodSensorRepository.kt) — main-safe suspend, Flow, Result
- [BadSensor.kt](./examples/BadSensor.kt) — common Kotlin/Android anti-patterns annotated

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `NullPointerException` from Kotlin code | `!!` or Java interop returning null | Replace `!!` with `?.`/`?:`, annotate Java API with `@Nullable` |
| Flow stops updating after screen rotation | Collecting outside `repeatOnLifecycle` | Wrap collection in `repeatOnLifecycle(STARTED)` |
| ViewModel leaks / coroutine keeps running | `GlobalScope.launch` or wrong scope | Use `viewModelScope`; cancel scope when done |
| Recomposition storm in Compose | Passing unstable objects / entire state to leaf composable | Pass only needed fields; use `@Stable` / `@Immutable`; `derivedStateOf` |
| Hilt `@Inject` not found | Missing `@HiltViewModel` or component annotation | Add `@HiltViewModel`; ensure module is `@InstallIn` correct component |
| Coroutine exception silently swallowed | `async` exception not awaited | `await()` the `Deferred`, or add `CoroutineExceptionHandler` |

---

## References

- [Kotlin Idioms](https://kotlinlang.org/docs/idioms.html)
- [Android Kotlin Style Guide](https://developer.android.com/kotlin/style-guide)
- [Android Architecture Guide](https://developer.android.com/topic/architecture)
- [Kotlin Coroutines Guide](https://kotlinlang.org/docs/coroutines-guide.html)
- [Jetpack Compose — Thinking in Compose](https://developer.android.com/develop/ui/compose/mental-model)
- [Hilt DI Guide](https://developer.android.com/training/dependency-injection/hilt-android)
- Internal skill: [java-code-writing](../java-code-writing/SKILL.md) — Android Framework / System Service layer
