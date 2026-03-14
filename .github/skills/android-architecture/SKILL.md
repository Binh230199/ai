---
name: android-architecture
description: >
  Use when designing, implementing, or reviewing Android app architecture —
  MVVM or MVI patterns, Clean Architecture layer separation (data/domain/presentation),
  Hilt dependency injection, feature modularization, and Repository pattern.
  Applies to Android Studio (Gradle) and AOSP (Soong) projects targeting AAOS.
argument-hint: <feature-or-module-name> [design|implement|review]
---

# Android Architecture

Expert guidance for structuring production-quality Android applications using
**Clean Architecture**, **MVVM / MVI**, and **Hilt dependency injection**.
Follows the [Android Architecture Recommendations](https://developer.android.com/topic/architecture)
and [Now in Android](https://github.com/android/nowinandroid) reference app patterns.

---

## When to Use This Skill

- Designing a new feature module from scratch.
- Reviewing or refactoring architecture — layering violations, god classes, leaking dependencies.
- Setting up Hilt modules, scoping bindings, or writing test overrides.
- Deciding between MVVM and MVI, or migrating from one to the other.
- Planning multi-module project structure (modularization strategy).

---

## Layer Model

```
┌─────────────────────────────────┐
│        Presentation Layer       │  UI (Compose/Views) + ViewModel
├─────────────────────────────────┤
│          Domain Layer           │  Use Cases (Interactors) + Entities
├─────────────────────────────────┤
│           Data Layer            │  Repositories + DataSources (Room/Retrofit/DataStore)
└─────────────────────────────────┘
```

**Dependency rule**: outer layers depend on inner, never the reverse.
- Presentation → Domain ← Data
- Domain contains **no Android framework imports**.

---

## MVVM Pattern

### ViewModel — state holder

```kotlin
@HiltViewModel
class MediaListViewModel @Inject constructor(
    private val getMediaItems: GetMediaItemsUseCase,  // domain
) : ViewModel() {

    private val _uiState = MutableStateFlow<MediaListUiState>(MediaListUiState.Loading)
    val uiState: StateFlow<MediaListUiState> = _uiState.asStateFlow()

    init {
        loadMedia()
    }

    fun loadMedia() {
        viewModelScope.launch {
            _uiState.value = MediaListUiState.Loading
            getMediaItems()
                .onSuccess { items -> _uiState.value = MediaListUiState.Success(items) }
                .onFailure { err -> _uiState.value = MediaListUiState.Error(err.message) }
        }
    }
}

sealed interface MediaListUiState {
    data object Loading : MediaListUiState
    data class Success(val items: List<MediaItem>) : MediaListUiState
    data class Error(val message: String?) : MediaListUiState
}
```

**Rules**
- `UiState` is a single sealed interface/class — never multiple separate `LiveData` booleans.
- Expose `StateFlow`, not `MutableStateFlow`, to the UI.
- Business logic lives in Use Cases, not in ViewModel.
- Keep ViewModel test-friendly — constructor-inject all dependencies.

---

## MVI Pattern

Use MVI when the UI has complex multi-source state that benefits from a single
unidirectional data flow with explicit events and effects.

```kotlin
// Contracts
sealed interface SearchIntent {
    data class Query(val text: String) : SearchIntent
    data object Retry : SearchIntent
}

data class SearchUiState(
    val query: String = "",
    val results: List<SearchResult> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
)

sealed interface SearchEffect {
    data class NavigateTo(val destination: String) : SearchEffect
    data class ShowSnackbar(val message: String) : SearchEffect
}

@HiltViewModel
class SearchViewModel @Inject constructor(
    private val searchUseCase: SearchUseCase,
) : ViewModel() {

    private val _uiState = MutableStateFlow(SearchUiState())
    val uiState: StateFlow<SearchUiState> = _uiState.asStateFlow()

    private val _effects = MutableSharedFlow<SearchEffect>()
    val effects: SharedFlow<SearchEffect> = _effects.asSharedFlow()

    fun dispatch(intent: SearchIntent) {
        when (intent) {
            is SearchIntent.Query -> onQuery(intent.text)
            SearchIntent.Retry   -> retry()
        }
    }

    private fun onQuery(text: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(query = text, isLoading = true, error = null) }
            searchUseCase(text)
                .onSuccess { results ->
                    _uiState.update { it.copy(results = results, isLoading = false) }
                }
                .onFailure { e ->
                    _uiState.update { it.copy(isLoading = false, error = e.message) }
                    _effects.emit(SearchEffect.ShowSnackbar(e.message ?: "Unknown error"))
                }
        }
    }
}
```

**Rules**
- One-shot side effects go in `SharedFlow` (not `StateFlow`).
- Collect effects inside `LaunchedEffect` tied to lifecycleScope — use `repeatOnLifecycle`.
- Never use a `Channel` for effects unless you need backpressure semantics.

---

## Clean Architecture: Domain Layer

```kotlin
// Entity (pure Kotlin — no Android imports)
data class MediaItem(
    val id: String,
    val title: String,
    val durationMs: Long,
    val artworkUrl: String,
)

// Use Case
class GetMediaItemsUseCase @Inject constructor(
    private val mediaRepository: MediaRepository,  // interface
) {
    suspend operator fun invoke(): Result<List<MediaItem>> =
        runCatching { mediaRepository.getMediaItems() }
}

// Repository interface (domain owns the interface)
interface MediaRepository {
    suspend fun getMediaItems(): List<MediaItem>
    fun observeMediaItems(): Flow<List<MediaItem>>
}
```

**Rules**
- Use cases have a single public method — `invoke()`.
- Entities are plain `data class` with no framework dependencies.
- Repository _interfaces_ live in the domain layer; _implementations_ live in the data layer.

---

## Clean Architecture: Data Layer

```kotlin
// Repository implementation
class MediaRepositoryImpl @Inject constructor(
    private val remoteDataSource: MediaRemoteDataSource,
    private val localDataSource: MediaLocalDataSource,
    private val ioDispatcher: CoroutineDispatcher,  // injected, not hardcoded
) : MediaRepository {

    override suspend fun getMediaItems(): List<MediaItem> =
        withContext(ioDispatcher) {
            try {
                val remote = remoteDataSource.fetchMedia()
                localDataSource.upsertAll(remote)
                remote
            } catch (e: IOException) {
                localDataSource.getAll()
            }
        }

    override fun observeMediaItems(): Flow<List<MediaItem>> =
        localDataSource.observeAll()
}
```

**Rules**
- Repository implementations are in the data layer, bound to the domain interface via Hilt.
- Inject `CoroutineDispatcher` — never call `Dispatchers.IO` directly in data layer classes.
- Map DTOs to domain entities in the data layer; domain entities never have JSON annotations.

---

## Hilt Dependency Injection

### Application entry point

```kotlin
@HiltAndroidApp
class MyApp : Application()
```

### Module

```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class MediaRepositoryModule {

    @Binds
    @Singleton
    abstract fun bindMediaRepository(impl: MediaRepositoryImpl): MediaRepository
}

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideRetrofit(): Retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .addConverterFactory(Json.asConverterFactory("application/json".toMediaType()))
        .build()
}

@Module
@InstallIn(SingletonComponent::class)
object DispatcherModule {

    @Provides
    @IoDispatcher
    fun provideIoDispatcher(): CoroutineDispatcher = Dispatchers.IO
}

// Custom qualifier
@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class IoDispatcher
```

### Scoping guide

| Scope | Annotation | Lifetime |
|---|---|---|
| App-wide singleton | `@Singleton` | App process |
| Per-Activity | `@ActivityScoped` | Single Activity instance |
| Per-Fragment | `@FragmentScoped` | Single Fragment instance |
| Per-ViewModel | `@ViewModelScoped` | ViewModel lifetime |

**Rules**
- Use `@Singleton` only for stateless services or caches that must be shared app-wide.
- Prefer `@ViewModelScoped` for objects that are logically scoped to a screen's data.
- Never inject `Activity` into a `@Singleton` — causes memory leaks.

---

## Feature Modularization

### Recommended module graph

```
:app
 ├── :feature:home
 ├── :feature:media
 ├── :feature:settings
 ├── :core:ui           (shared Compose components, theme)
 ├── :core:data         (Room database, Retrofit, DataStore)
 ├── :core:domain       (shared entities, use case base)
 ├── :core:network      (Retrofit setup, interceptors)
 └── :core:testing      (test helpers, fakes)
```

### Module type rules

| Module type | Can depend on | Cannot depend on |
|---|---|---|
| `:feature:*` | `:core:*` | Other `:feature:*` directly |
| `:core:data` | `:core:network`, `:core:domain` | `:feature:*`, `:app` |
| `:core:domain` | Nothing Android-specific | `:core:data`, `:feature:*` |
| `:app` | All modules | — |

**Rules**
- Features communicate via shared `:core:domain` contracts, not direct references.
- Shared UI components go in `:core:ui`, not duplicated in each feature.
- Each module has its own Hilt `@Module` installed in the appropriate component.

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

### Step 1: Define the layer boundaries
Separate code into `data/`, `domain/`, and `presentation/` packages.

### Step 2: Create the Repository
Implement the Repository interface in the data layer; inject dependencies with Hilt.

### Step 3: Write UseCases (domain layer)
Implement single-responsibility use cases that call repository methods.

### Step 4: Connect the ViewModel
Inject use cases into the ViewModel; expose UI state as `StateFlow<UiState>`.

### Step 5: Observe in Composable / Fragment
Collect the `StateFlow` with `collectAsStateWithLifecycle()` or `repeatOnLifecycle`.


## Troubleshooting

- **ViewModel survives configuration change but data is wrong** — ensure `StateFlow` is initialized lazily in `init {...}` and not re-created on each `viewModel` call.
- **Hilt `@Inject` constructor not found** — check that the class is annotated with `@HiltViewModel` or is in a Hilt module; rebuild the project.
- **Use case referencing UI model** — domain layer must not reference Android or UI types; extract a pure domain model.
- **Repository blocking the UI thread** — all repository operations must be `suspend` or return `Flow`; call from `viewModelScope` with `Dispatchers.IO`.


## Pre-Commit Checklist

- [ ] ViewModel only depends on domain layer (Use Cases / interfaces).
- [ ] No Android imports in domain entities or use cases.
- [ ] Repository interface in domain; implementation in data.
- [ ] `CoroutineDispatcher` injected, not hardcoded.
- [ ] `UiState` is a single sealed type, not multiple booleans.
- [ ] Effects emitted via `SharedFlow`, not `StateFlow`.
- [ ] Hilt scoping matches the lifetime of the dependency.
- [ ] No circular module dependencies.
- [ ] Every Use Case has a corresponding unit test.

---

## References

- [Android Architecture Guide](https://developer.android.com/topic/architecture)
- [Now in Android reference app](https://github.com/android/nowinandroid)
- [Hilt DI Guide](https://developer.android.com/training/dependency-injection/hilt-android)
- [Guide to app modularization](https://developer.android.com/topic/modularization)
