---
name: android-kotlin-coroutines
description: >
  Use when writing, reviewing, or debugging asynchronous Kotlin code using
  Coroutines and Flow in Android apps. Covers suspend functions, CoroutineScope
  and Job, Dispatchers, structured concurrency, exception handling, Flow operators,
  StateFlow, SharedFlow, Channels, lifecycle-safe collection patterns, and testing
  with TestCoroutineDispatcher and Turbine. Applies to AAOS Android app development.
argument-hint: <class-or-function> [write|review|debug|migrate]
---

# Kotlin Coroutines & Flow

Expert reference for asynchronous programming with Kotlin Coroutines and Flow in
Android applications, following Roman Elizarov's
[Structured Concurrency](https://elizarov.medium.com/structured-concurrency-722d765aa952) principles
and the official [Kotlin Coroutines Guide](https://kotlinlang.org/docs/coroutines-guide.html).

Standards baseline: **Kotlin Coroutines 1.8+** · **Android Lifecycle 2.8+**.

---

## When to Use This Skill

- Writing `suspend` functions or `Flow` producers for data/network/disk operations.
- Reviewing coroutine lifecycle — scope leaks, cancelled jobs, unconsumed exceptions.
- Migrating callbacks or RxJava streams to coroutines / Flow.
- Designing complex async pipelines (combining, debouncing, retrying flows).
- Testing coroutine-based code with `runTest`, `advanceUntilIdle`, or Turbine.
- Choosing between StateFlow, SharedFlow, and Channel.

---

## Fundamentals

### Suspend functions

```kotlin
// Launch coroutine from ViewModel
viewModelScope.launch {
    val result = fetchData()   // suspend — non-blocking, frees Dispatcher thread
    updateUi(result)
}

suspend fun fetchData(): Data = withContext(Dispatchers.IO) {
    apiService.getData()
}
```

**Rules**
- Mark a function `suspend` only if it suspends; otherwise it is a normal function.
- Don't mark a function `suspend` just to run it on a coroutine — use `withContext`.
- `withContext` does NOT create a new coroutine — it switches dispatcher within the current one.

---

## Coroutine Builders

| Builder | Behaviour | Use case |
|---|---|---|
| `launch` | Fire-and-forget; returns `Job` | Side effects (update DB, emit event) |
| `async` | Returns `Deferred<T>` | Parallel work with a result |
| `runBlocking` | Blocks calling thread | Test glue code, `main()` entrypoint |
| `coroutineScope` | Suspending scope; waits for children | Group parallel work; propagates cancel |
| `supervisorScope` | Like `coroutineScope` but child failures don't cancel siblings | Parallel independent tasks |

```kotlin
// Parallel work with structured concurrency
suspend fun loadDashboard(): Dashboard = coroutineScope {
    val music = async { musicRepository.getNowPlaying() }
    val weather = async { weatherRepository.getCurrent() }
    Dashboard(music = music.await(), weather = weather.await())
}
```

---

## Dispatchers

| Dispatcher | Thread pool | Best for |
|---|---|---|
| `Dispatchers.Main` | Main (UI) thread | UI updates, collect StateFlow in ViewModel |
| `Dispatchers.IO` | Shared thread pool (64) | Network, disk, database |
| `Dispatchers.Default` | Shared CPU-bound pool | CPU-intensive: sorting, parsing, JSON |
| `Dispatchers.Unconfined` | Caller thread (then resumes anywhere) | Tests; avoid in production |

**Rules**
- Never call `Dispatchers.IO` directly — inject as `CoroutineDispatcher`:

```kotlin
// Injection (Hilt)
@Qualifier @Retention(AnnotationRetention.BINARY) annotation class IoDispatcher
@Qualifier @Retention(AnnotationRetention.BINARY) annotation class DefaultDispatcher

@Provides @IoDispatcher fun provideIo(): CoroutineDispatcher = Dispatchers.IO
@Provides @DefaultDispatcher fun provideDefault(): CoroutineDispatcher = Dispatchers.Default
```

---

## CoroutineScope & Job

### Structured Concurrency rule

Every coroutine must be launched in a scope whose lifetime matches where it is used.
A leaked scope (scope that outlives its owner) is a bug.

```kotlin
// Android scopes (provided by Jetpack)
viewModelScope     // cancelled when ViewModel.onCleared()
lifecycleScope     // cancelled when Activity/Fragment destroyed
```

### Custom scope

```kotlin
class MediaSyncService @Inject constructor(
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher,
) {
    private val scope = CoroutineScope(SupervisorJob() + ioDispatcher)

    fun startSync() {
        scope.launch { /* ... */ }
    }

    fun stopSync() {
        scope.cancel()   // cancel all children
    }
}
```

**Rules**
- Use `SupervisorJob` when child failures should not cancel sibling coroutines.
- Always cancel a custom scope in the appropriate lifecycle callback (`onDestroy`, `onCleared`).
- Never use `GlobalScope` — it lives for the entire process and cancels nothing.

---

## Exception Handling

```kotlin
// In launch — exceptions propagate to scope; handle via CoroutineExceptionHandler
val handler = CoroutineExceptionHandler { _, throwable ->
    Log.e(TAG, "Unhandled coroutine exception", throwable)
}
viewModelScope.launch(handler) {
    riskyOperation()
}

// In async — exception is deferred until .await()
val deferred = async { riskyOperation() }
try {
    deferred.await()
} catch (e: Exception) {
    // handle
}

// supervisorScope — isolate failure
supervisorScope {
    launch { fetchA() }  // fails silently without cancelling fetchB
    launch { fetchB() }
}
```

**Rules**
- `CancellationException` must **never** be caught and swallowed — it signals cancellation.
- Only catch `CancellationException` to do cleanup; always re-throw it.
- Prefer `Result<T>` return types over throwing unchecked exceptions from suspend functions.

```kotlin
// Correct cancellation-safe pattern
try {
    suspendOperation()
} catch (e: CancellationException) {
    throw e      // re-throw — do not swallow!
} catch (e: Exception) {
    // handle business errors
}
```

---

## Flow

### Cold Flow (producer runs per collector)

```kotlin
fun fetchItems(): Flow<List<Item>> = flow {
    while (true) {
        emit(repository.getAll())
        delay(5_000)
    }
}
```

### Key operators

```kotlin
itemsFlow
    .filter { it.isActive }
    .map { it.toDomain() }
    .debounce(300)                            // wait 300 ms of silence
    .distinctUntilChanged()                   // skip repeated equal values
    .catch { e -> Log.e(TAG, "Error", e) }    // recover from upstream errors
    .onEach { analytics.track(it) }           // side effects
    .launchIn(viewModelScope)                 // terminal — launch collection
```

### Combining flows

```kotlin
// Combine latest values from two flows
combine(userFlow, settingsFlow) { user, settings ->
    DashboardState(user, settings)
}.collect { render(it) }

// Flat-map latest (like RxJava switchMap)
searchQuery
    .debounce(300)
    .flatMapLatest { query -> searchRepository.search(query) }
    .collect { showResults(it) }

// Zip — pair emissions one-to-one
flow1.zip(flow2) { a, b -> a + b }.collect { ... }
```

---

## StateFlow & SharedFlow

### StateFlow — UI state holder (hot, single value)

```kotlin
// In ViewModel
private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
val uiState: StateFlow<UiState> = _uiState.asStateFlow()

// Update
_uiState.value = UiState.Success(items)          // replace
_uiState.update { current -> current.copy(...) } // atomic update

// In Compose — lifecycle-aware
val state by viewModel.uiState.collectAsStateWithLifecycle()
```

### SharedFlow — one-time events (hot, no cached value default)

```kotlin
// In ViewModel
private val _events = MutableSharedFlow<UiEvent>()
val events: SharedFlow<UiEvent> = _events.asSharedFlow()

fun sendError(msg: String) {
    viewModelScope.launch { _events.emit(UiEvent.ShowSnackbar(msg)) }
}

// Collect in Fragment
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.events.collect { event ->
            when (event) {
                is UiEvent.ShowSnackbar -> showSnackbar(event.message)
                is UiEvent.Navigate -> findNavController().navigate(event.destination)
            }
        }
    }
}
```

### Converting cold to hot (sharing upstream)

```kotlin
// Share across all collectors; replay last value on new subscriber
val sharedItems: StateFlow<List<Item>> = repository.observeItems()
    .stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),  // keep 5s after last subscriber
        initialValue = emptyList(),
    )
```

**Rules**
- Use `SharingStarted.WhileSubscribed(5_000)` — keeps flow alive 5 s after rotation to avoid restart.
- Never use `SharingStarted.Eagerly` in production — it wastes resources when no one is subscribed.
- Never expose `MutableStateFlow` or `MutableSharedFlow` to the UI layer.

---

## Channels

Use channels only for fan-out / fan-in patterns, not as a replacement for SharedFlow
for events.

```kotlin
val channel = Channel<WorkItem>(capacity = Channel.UNLIMITED)

// Producer
launch { channel.send(WorkItem("task1")) }

// Consumer
launch { for (item in channel) process(item) }
```

---

## Lifecycle-Safe Collection

```kotlin
// In Activity / Fragment — REQUIRED pattern
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { render(it) }
    }
}

// In Compose — built-in lifecycle safety
val uiState by viewModel.uiState.collectAsStateWithLifecycle()
```

**Rules**
- **Never** collect in `lifecycleScope.launch { flow.collect { } }` without `repeatOnLifecycle` — it keeps collecting in the background.
- **Never** use `launchWhenStarted` — deprecated; use `repeatOnLifecycle(STARTED)`.

---

## callbackFlow — Convert Callbacks to Flow

```kotlin
fun CarPropertyManager.observeTemperature(zone: Int): Flow<Float> = callbackFlow {
    val callback = object : CarPropertyManager.CarPropertyEventCallback {
        override fun onChangeEvent(event: CarPropertyValue<*>) {
            trySend(event.value as Float)
        }
        override fun onErrorEvent(propId: Int, zone: Int) {
            close(IOException("Property error: $propId"))
        }
    }
    registerCallback(callback, VehiclePropertyIds.HVAC_TEMPERATURE_SET, SENSOR_RATE_ONCHANGE)
    awaitClose { unregisterCallback(callback) }
}
```

---

## Testing

### runTest + advanceUntilIdle

```kotlin
@Test
fun `emits updated state after load`() = runTest {
    val viewModel = MyViewModel(fakeRepository)

    viewModel.uiState.test {
        assertThat(awaitItem()).isEqualTo(UiState.Loading)
        assertThat(awaitItem()).isEqualTo(UiState.Success(expectedData))
        cancelAndIgnoreRemainingEvents()
    }
}
```

### Dispatcher injection in tests

```kotlin
class MainDispatcherRule(
    val dispatcher: TestCoroutineDispatcher = StandardTestDispatcher(),
) : TestWatcher() {
    override fun starting(d: Description) { Dispatchers.setMain(dispatcher) }
    override fun finished(d: Description) { Dispatchers.resetMain() }
}

// In test class
@get:Rule val mainDispatcherRule = MainDispatcherRule()

// Advance time
mainDispatcherRule.dispatcher.advanceTimeBy(5_000)  // advance 5 seconds
mainDispatcherRule.dispatcher.advanceUntilIdle()    // drain all pending tasks
```

---

## RxJava / Callback Migration Reference

| RxJava | Coroutines / Flow |
|---|---|
| `Observable<T>` | `Flow<T>` |
| `Single<T>` | `suspend fun: T` |
| `Completable` | `suspend fun: Unit` |
| `Maybe<T>` | `suspend fun: T?` |
| `BehaviorSubject<T>` | `MutableStateFlow<T>` |
| `PublishSubject<T>` | `MutableSharedFlow<T>` |
| `subscribeOn(io)` | `withContext(Dispatchers.IO)` |
| `observeOn(main)` | `withContext(Dispatchers.Main)` |
| `switchMap` | `flatMapLatest` |
| `merge` | `merge(flow1, flow2)` |
| `zip` | `zip` or `combine` |

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

### Step 1: Add coroutines dependencies
Add `kotlinx-coroutines-android` and `kotlinx-coroutines-core` to `build.gradle.kts`.

### Step 2: Launch coroutines in the correct scope
Use `viewModelScope` in ViewModels; `lifecycleScope` in Fragments/Activities.

### Step 3: Switch dispatchers for blocking work
Use `Dispatchers.IO` for I/O operations; `Dispatchers.Default` for CPU-intensive tasks.

### Step 4: Collect Flows lifecycle-safely
Use `repeatOnLifecycle(Lifecycle.State.STARTED)` — never `lifecycleScope.launch` for UI collection.

### Step 5: Test coroutines
Use `TestCoroutineScheduler` + `runTest {}` for deterministic tests; Turbine for Flow assertions.


## Troubleshooting

- **`CancellationException` swallowing** — never catch bare `Exception` in coroutines; always rethrow `CancellationException`.
- **Flow not updating UI** — collection must be inside `repeatOnLifecycle(STARTED)`; using `lifecycleScope.launch` directly does not stop on background.
- **`SharedFlow` dropped events** — `replay = 0` means new collectors miss past events; set `replay = 1` or use `StateFlow` for last-value semantics.
- **Tests are flaky with coroutines** — use `TestCoroutineScheduler` and `advanceUntilIdle()`; never use `Thread.sleep()` in coroutine tests.


## Pre-Commit Checklist

- [ ] `Dispatchers.IO` / `Default` are injected, not hardcoded.
- [ ] No `GlobalScope.launch` — use `viewModelScope`, `lifecycleScope`, or injected scope.
- [ ] `CancellationException` is never caught and swallowed.
- [ ] `MutableStateFlow` / `MutableSharedFlow` unexposed — only read-only `StateFlow`/ `SharedFlow` in public API.
- [ ] Flow collected with `repeatOnLifecycle` in Activity/Fragment (not bare `launch`).
- [ ] `callbackFlow` has `awaitClose` block to unregister listener.
- [ ] `stateIn` uses `WhileSubscribed(5_000)` unless there is a specific reason otherwise.
- [ ] All coroutine-based code has a corresponding `runTest` unit test.

---

## References

- [Kotlin Coroutines Guide](https://kotlinlang.org/docs/coroutines-guide.html)
- [Android Coroutines Best Practices](https://developer.android.com/kotlin/coroutines/coroutines-best-practices)
- [Flow documentation](https://kotlinlang.org/docs/flow.html)
- [Structured Concurrency — Roman Elizarov](https://elizarov.medium.com/structured-concurrency-722d765aa952)
- [Turbine](https://github.com/cashapp/turbine)
- [Testing Coroutines](https://developer.android.com/kotlin/coroutines/test)
