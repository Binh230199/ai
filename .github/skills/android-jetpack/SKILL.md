---
name: android-jetpack
description: >
  Use when implementing or reviewing Jetpack library integrations in Android apps:
  Navigation Component, Room database, DataStore, WorkManager, Paging 3, and
  Lifecycle-aware components (LiveData, StateFlow, repeatOnLifecycle).
  Covers both Android Studio (Gradle) and AOSP (Soong) on Android Automotive / AAOS.
argument-hint: <library-or-feature> [room|datastore|navigation|workmanager|paging]
---

# Android Jetpack Libraries

Expert integration patterns for core Jetpack libraries used in Android Automotive
and standard Android apps. Follows [Jetpack official guides](https://developer.android.com/jetpack)
and the [Now in Android](https://github.com/android/nowinandroid) reference practices.

---

## When to Use This Skill

- Adding or reviewing Room entities, DAOs, migrations, or relations.
- Implementing offline-first data sync with Room + Retrofit.
- Choosing between DataStore (Preferences vs Proto) and SharedPreferences.
- Setting up WorkManager for background jobs, constraints, and chaining.
- Implementing infinite scroll / paginated lists with Paging 3.
- Lifecycle collection of Flow / LiveData (repeatOnLifecycle, collectAsStateWithLifecycle).

---

## Room — Local Database

### Setup

```kotlin
// Entity
@Entity(tableName = "media_items")
data class MediaItemEntity(
    @PrimaryKey val id: String,
    val title: String,
    val durationMs: Long,
    val artworkUrl: String,
    val cachedAt: Long = System.currentTimeMillis(),
)

// DAO
@Dao
interface MediaItemDao {
    @Query("SELECT * FROM media_items ORDER BY title ASC")
    fun observeAll(): Flow<List<MediaItemEntity>>   // Flow for reactive updates

    @Query("SELECT * FROM media_items WHERE id = :id")
    suspend fun getById(id: String): MediaItemEntity?

    @Upsert
    suspend fun upsertAll(items: List<MediaItemEntity>)

    @Query("DELETE FROM media_items WHERE cachedAt < :threshold")
    suspend fun deleteOlderThan(threshold: Long)
}

// Database
@Database(
    entities = [MediaItemEntity::class],
    version = 2,
    exportSchema = true,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun mediaItemDao(): MediaItemDao
}
```

### Dependency injection (Hilt)

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, "app_db")
            .addMigrations(MIGRATION_1_2)
            .build()

    @Provides
    fun provideMediaItemDao(db: AppDatabase): MediaItemDao = db.mediaItemDao()
}
```

### Migrations

```kotlin
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE media_items ADD COLUMN cachedAt INTEGER NOT NULL DEFAULT 0")
    }
}
```

**Rules**
- Always `exportSchema = true` and commit the schema JSON to version control.
- Use `@Upsert` (Room 2.5+) instead of `@Insert(onConflict = REPLACE)`.
- Return `Flow` from queries for reactive updates; use `suspend` for one-shot reads/writes.
- Run migrations in CI: test with `MigrationTestHelper`.
- Never access `RoomDatabase` on the main thread.

### Relations

```kotlin
data class ArtistWithAlbums(
    @Embedded val artist: ArtistEntity,
    @Relation(
        parentColumn = "id",
        entityColumn = "artistId",
    )
    val albums: List<AlbumEntity>,
)

@Transaction
@Query("SELECT * FROM artists")
fun observeArtistsWithAlbums(): Flow<List<ArtistWithAlbums>>
```

---

## DataStore — Preferences & Settings

### Preferences DataStore (key-value)

```kotlin
private val Context.dataStore by preferencesDataStore(name = "settings")

class SettingsRepository @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    companion object {
        val THEME_KEY = intPreferencesKey("theme")
        val NOTIFICATIONS_KEY = booleanPreferencesKey("notifications_enabled")
    }

    val theme: Flow<Int> = context.dataStore.data
        .catch { e -> if (e is IOException) emit(emptyPreferences()) else throw e }
        .map { prefs -> prefs[THEME_KEY] ?: 0 }

    suspend fun setTheme(theme: Int) {
        context.dataStore.edit { it[THEME_KEY] = theme }
    }
}
```

### Proto DataStore (type-safe, structured)

Use Proto DataStore when you have complex settings objects. Define a `.proto` schema
and use the generated classes. Prefer it over Preferences DataStore for non-trivial settings.

**Rules**
- Prefer DataStore over SharedPreferences in new code — it is coroutine-safe.
- Always add `.catch { e -> if (e is IOException) emit(emptyPreferences()) }` to handle corruption.
- Inject DataStore via Hilt — never pass context to call site.

---

## WorkManager — Background Tasks

### Worker (coroutine-based)

```kotlin
@HiltWorker
class SyncMediaWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val syncRepository: MediaSyncRepository,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            syncRepository.syncAll()
            Result.success()
        } catch (e: Exception) {
            if (runAttemptCount < 3) Result.retry() else Result.failure()
        }
    }
}
```

### Enqueue with constraints

```kotlin
val constraints = Constraints.Builder()
    .setRequiredNetworkType(NetworkType.CONNECTED)
    .setRequiresBatteryNotLow(true)
    .build()

val syncRequest = PeriodicWorkRequestBuilder<SyncMediaWorker>(
    repeatInterval = 6,
    repeatIntervalTimeUnit = TimeUnit.HOURS,
).setConstraints(constraints)
 .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
 .build()

WorkManager.getInstance(context).enqueueUniquePeriodicWork(
    "sync_media",
    ExistingPeriodicWorkPolicy.KEEP,
    syncRequest,
)
```

**Rules**
- Use `HiltWorker` + `@AssistedInject` for dependency injection in Workers.
- Always use `enqueueUniqueWork` or `enqueueUniquePeriodicWork` to avoid duplicate jobs.
- Implement retry logic with exponential backoff; limit `runAttemptCount`.
- For immediate one-time work use `OneTimeWorkRequest`; for recurring use `PeriodicWorkRequest`.

---

## Paging 3 — Infinite Lists

### PagingSource

```kotlin
class MediaPagingSource @Inject constructor(
    private val apiService: MediaApiService,
) : PagingSource<Int, MediaItem>() {

    override suspend fun load(params: LoadParams<Int>): LoadResult<Int, MediaItem> {
        val page = params.key ?: 1
        return try {
            val response = apiService.getMedia(page = page, size = params.loadSize)
            LoadResult.Page(
                data = response.items.map { it.toDomain() },
                prevKey = if (page == 1) null else page - 1,
                nextKey = if (response.items.isEmpty()) null else page + 1,
            )
        } catch (e: Exception) {
            LoadResult.Error(e)
        }
    }

    override fun getRefreshKey(state: PagingState<Int, MediaItem>): Int? =
        state.anchorPosition?.let { anchor ->
            state.closestPageToPosition(anchor)?.prevKey?.plus(1)
                ?: state.closestPageToPosition(anchor)?.nextKey?.minus(1)
        }
}
```

### ViewModel + Compose

```kotlin
@HiltViewModel
class MediaListViewModel @Inject constructor(
    private val pagingSource: MediaPagingSource,
) : ViewModel() {
    val pagingData: Flow<PagingData<MediaItem>> = Pager(
        config = PagingConfig(pageSize = 20, prefetchDistance = 5),
        pagingSourceFactory = { pagingSource },
    ).flow.cachedIn(viewModelScope)
}

// Compose
@Composable
fun MediaListScreen(viewModel: MediaListViewModel = hiltViewModel()) {
    val pagingItems = viewModel.pagingData.collectAsLazyPagingItems()

    LazyColumn {
        items(count = pagingItems.itemCount, key = { pagingItems.peek(it)?.id ?: it }) { index ->
            val item = pagingItems[index]
            if (item != null) MediaItemRow(item = item)
        }

        pagingItems.apply {
            when (loadState.append) {
                is LoadState.Loading -> item { CircularProgressIndicator() }
                is LoadState.Error -> item { RetryButton(onClick = ::retry) }
                else -> Unit
            }
        }
    }
}
```

---

## Lifecycle — Safe Collection Patterns

### Fragment / Activity

```kotlin
// Lifecycle-safe — stops collection when STOPPED, restarts when STARTED
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { render(it) }
    }
}
```

### Compose

```kotlin
// collectAsStateWithLifecycle automatically uses STARTED lifecycle
val uiState by viewModel.uiState.collectAsStateWithLifecycle()
```

### LiveData → StateFlow migration

```kotlin
// Legacy LiveData (avoid in new code)
viewModel.items.observe(viewLifecycleOwner) { render(it) }

// Modern replacement
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.items.collect { render(it) }
    }
}
```

**Rules**
- Never use `lifecycleScope.launchWhenStarted` — it is deprecated; use `repeatOnLifecycle`.
- Never collect `Flow` in a plain `lifecycleScope.launch` without `repeatOnLifecycle` — it leaks.
- Use `collectAsStateWithLifecycle()` in Compose (not `collectAsState()`).

---

## AOSP — Jetpack in Android.bp

Jetpack libraries are available as AOSP prebuilts or AAOS platform libraries:

```soong
android_app {
    name: "MyApp",
    static_libs: [
        // AndroidX (bundled as AAPT2 AARs in AOSP prebuilts)
        "androidx.lifecycle_lifecycle-viewmodel-ktx",
        "androidx.room_room-runtime",
        "androidx.room_room-ktx",
        "androidx.work_work-runtime-ktx",
        "androidx.paging_paging-runtime",
        "androidx.datastore_datastore-preferences",
        // Hilt
        "hilt_android",
    ],
    plugins: [
        "room_annotation_processor",  // Room compiler
        "hilt_compiler",
    ],
    ...
}
```

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

### Step 1: Add Jetpack dependencies
Use the AndroidX BOM or version catalog (`libs.versions.toml`); keep versions centralized.

### Step 2: Define the data layer
Implement Room `@Entity`, `@Dao`, and `@Database`; or configure DataStore Proto/Preferences.

### Step 3: Create the Repository
Wrap Jetpack data sources; expose data as `Flow<T>` for reactive consumption.

### Step 4: Schedule background work (WorkManager)
Define a `CoroutineWorker`; enqueue with `WorkManager.getInstance().enqueue()` + constraints.

### Step 5: Observe in ViewModel / UI
Collect `Flow` in `viewModelScope`; expose as `StateFlow` to Compose or View-based UI.


## Troubleshooting

- **Room `IllegalStateException: Migration required`** — increment `DATABASE_VERSION` and provide a `Migration` object; or use `fallbackToDestructiveMigration()` for dev builds.
- **WorkManager not executing** — check `WorkInfo.State` via `getWorkInfoByIdLiveData()`; ensure battery optimization is not restricting the app.
- **`DataStore IOException` on first read** — DataStore file may be corrupted; handle the exception and call `updateData { defaultProto }` to reset.
- **Paging `LoadState` stuck in `Loading`** — the `PagingSource.load()` is not returning a `LoadResult.Error` on failure; add proper error handling.


## Pre-Commit Checklist

- [ ] Room: schema exported, migrations tested, `@Transaction` on relations.
- [ ] DataStore: `catch(IOException)` guard present, injected via Hilt.
- [ ] WorkManager: unique work name, retry logic, constraints defined.
- [ ] Paging: `getRefreshKey` implemented, `LoadState` handled in UI.
- [ ] Flow collected inside `repeatOnLifecycle` or `collectAsStateWithLifecycle`.
- [ ] No `LiveData.observe()` without proper `viewLifecycleOwner`.
- [ ] Database operations on IO dispatcher only.

---

## References

- [Room documentation](https://developer.android.com/training/data-storage/room)
- [DataStore documentation](https://developer.android.com/topic/libraries/architecture/datastore)
- [WorkManager guide](https://developer.android.com/topic/libraries/architecture/workmanager)
- [Paging 3 guide](https://developer.android.com/topic/libraries/architecture/paging/v3-overview)
- [Lifecycle guide](https://developer.android.com/topic/libraries/architecture/lifecycle)
