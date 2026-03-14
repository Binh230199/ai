---
name: android-testing
description: >
  Use when writing, reviewing, or debugging tests for Android applications:
  unit tests (JUnit4/5, MockK), ViewModel and Flow tests (Turbine), Hilt integration
  tests, UI tests (Espresso, Compose Test API), and screenshot tests (Paparazzi/Roborazzi).
  Covers both Android Studio (Gradle) and AOSP (Soong) test modules on AAOS targets.
argument-hint: <class-or-feature> [unit|viewmodel|integration|ui|compose|screenshot]
---

# Android Testing

Expert guidance for building a reliable, maintainable test suite for Android
applications following the testing pyramid: **unit → integration → UI**.

Standards baseline: **JUnit 4 / JUnit 5** · **MockK 1.13+** · **Turbine** · **Compose Test APIs**.

---

## When to Use This Skill

- Writing unit tests for pure logic, UseCases, Repositories, or utilities.
- Testing ViewModel state transitions and StateFlow / SharedFlow emissions.
- Setting up Hilt test components and fake bindings.
- Writing Compose UI tests (semantics-based assertions).
- Writing Espresso UI tests for legacy XML-based screens.
- Configuring screenshot tests (regression) with Paparazzi or Roborazzi.
- Adding a Room in-memory database test.

---

## Testing Pyramid

```
               ┌─────────────────────────┐
               │     UI Tests (slow)     │  Espresso / Compose Tests
               │  Real device/emulator   │  End-to-end user flows
               ├─────────────────────────┤
               │  Integration Tests      │  Hilt + Room in-memory
               │  (medium speed)         │  Multiple components together
               ├─────────────────────────┤
               │    Unit Tests (fast)    │  JUnit4/5 + MockK
               │  JVM only, no Android   │  Logic, ViewModels, UseCases
               └─────────────────────────┘
```

Target ratio: **70% unit · 20% integration · 10% UI**.

---

## Unit Tests — JUnit4 + MockK

### UseCase / Repository

```kotlin
class GetMediaItemsUseCaseTest {

    @MockK lateinit var mediaRepository: MediaRepository
    private lateinit var useCase: GetMediaItemsUseCase

    @BeforeEach
    fun setUp() {
        MockKAnnotations.init(this, relaxUnitFun = true)
        useCase = GetMediaItemsUseCase(mediaRepository)
    }

    @Test
    fun `returns items from repository when successful`() = runTest {
        val expected = listOf(MediaItem("1", "Song A", 180_000L, ""))
        coEvery { mediaRepository.getMediaItems() } returns expected

        val result = useCase()

        assertThat(result.isSuccess).isTrue()
        assertThat(result.getOrNull()).isEqualTo(expected)
        coVerify(exactly = 1) { mediaRepository.getMediaItems() }
    }

    @Test
    fun `returns failure when repository throws`() = runTest {
        coEvery { mediaRepository.getMediaItems() } throws IOException("Network error")

        val result = useCase()

        assertThat(result.isFailure).isTrue()
    }
}
```

### Mocking patterns

```kotlin
// Mock with default relaxed stubs
val repo = mockk<MediaRepository>(relaxed = true)

// Stub a suspend function
coEvery { repo.getMediaItems() } returns emptyList()

// Capture arguments
val slot = slot<String>()
coEvery { repo.save(capture(slot)) } just Runs
repo.save("hello")
assertThat(slot.captured).isEqualTo("hello")

// Verify call count
coVerify(exactly = 1) { repo.getMediaItems() }
verify(atLeast = 1) { analytics.track(any()) }
confirmVerified(repo)  // ensure no unexpected calls
```

---

## ViewModel Tests with Coroutines

```kotlin
@ExtendWith(CoroutinesTestExtension::class)  // custom; or use @get:Rule MainDispatcherRule
class MediaListViewModelTest {

    @MockK lateinit var getMediaItems: GetMediaItemsUseCase
    private lateinit var viewModel: MediaListViewModel

    // MainDispatcherRule swaps Dispatchers.Main with TestCoroutineDispatcher
    @get:Rule val mainDispatcherRule = MainDispatcherRule()

    @BeforeEach
    fun setUp() {
        MockKAnnotations.init(this, relaxUnitFun = true)
        viewModel = MediaListViewModel(getMediaItems)
    }

    @Test
    fun `uiState transitions from Loading to Success`() = runTest {
        val items = listOf(MediaItem("1", "Song", 0L, ""))
        coEvery { getMediaItems() } returns Result.success(items)

        viewModel.uiState.test {
            assertThat(awaitItem()).isInstanceOf(MediaListUiState.Loading::class.java)
            assertThat(awaitItem()).isEqualTo(MediaListUiState.Success(items))
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test
    fun `uiState emits Error on failure`() = runTest {
        coEvery { getMediaItems() } returns Result.failure(RuntimeException("oops"))

        viewModel.uiState.test {
            skipItems(1) // Loading
            val state = awaitItem()
            assertThat(state).isInstanceOf(MediaListUiState.Error::class.java)
            cancelAndIgnoreRemainingEvents()
        }
    }
}
```

### MainDispatcherRule (copy into `:core:testing`)

```kotlin
class MainDispatcherRule(
    val testDispatcher: TestCoroutineDispatcher = StandardTestDispatcher(),
) : TestWatcher() {
    override fun starting(description: Description) {
        Dispatchers.setMain(testDispatcher)
    }
    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
```

---

## Room In-Memory Tests

```kotlin
@RunWith(AndroidJUnit4::class)
class MediaItemDaoTest {

    private lateinit var db: AppDatabase
    private lateinit var dao: MediaItemDao

    @Before
    fun setUp() {
        db = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java,
        ).allowMainThreadQueries().build()
        dao = db.mediaItemDao()
    }

    @After
    fun tearDown() { db.close() }

    @Test
    fun upsert_and_observe() = runTest {
        val item = MediaItemEntity("1", "Song", 180_000L, "")
        dao.upsertAll(listOf(item))

        dao.observeAll().test {
            assertThat(awaitItem()).containsExactly(item)
            cancelAndIgnoreRemainingEvents()
        }
    }
}
```

---

## Hilt Integration Tests

```kotlin
@HiltAndroidTest
@RunWith(AndroidJUnit4::class)
class MediaRepositoryIntegrationTest {

    @get:Rule val hiltRule = HiltAndroidRule(this)

    @Inject lateinit var repository: MediaRepository

    @Before
    fun setUp() { hiltRule.inject() }

    @Test
    fun injects_repository_successfully() {
        assertThat(repository).isNotNull()
    }
}
```

### Replacing modules in tests

```kotlin
@UninstallModules(NetworkModule::class)
@HiltAndroidTest
class FakeNetworkTest {

    @Module
    @InstallIn(SingletonComponent::class)
    object FakeNetworkModule {
        @Provides
        fun provideApiService(): MediaApiService = FakeMediaApiService()
    }

    @get:Rule val hiltRule = HiltAndroidRule(this)
    @Inject lateinit var repository: MediaRepository

    @Before fun setUp() { hiltRule.inject() }
}
```

---

## Compose UI Tests

```kotlin
@RunWith(AndroidJUnit4::class)
class MediaListScreenTest {

    @get:Rule val composeTestRule = createComposeRule()

    @Test
    fun shows_items_when_state_is_success() {
        val items = listOf(MediaItem("1", "Song A", 180_000L, ""))
        val fakeViewModel = FakeMediaListViewModel(MediaListUiState.Success(items))

        composeTestRule.setContent {
            MyAppTheme { MediaListScreen(viewModel = fakeViewModel) }
        }

        composeTestRule.onNodeWithText("Song A").assertIsDisplayed()
    }

    @Test
    fun shows_loading_indicator() {
        composeTestRule.setContent {
            MyAppTheme { MediaListScreen(viewModel = FakeMediaListViewModel(MediaListUiState.Loading)) }
        }

        composeTestRule.onNodeWithTag("loading_indicator").assertIsDisplayed()
    }

    @Test
    fun click_item_triggers_navigation() {
        var clickedId: String? = null
        composeTestRule.setContent {
            MediaItemRow(item = MediaItem("1", "Song", 0L, ""), onItemClick = { clickedId = it })
        }

        composeTestRule.onNodeWithText("Song").performClick()

        assertThat(clickedId).isEqualTo("1")
    }
}
```

**Rules**
- Use `testTag()` modifier on key UI elements — not `contentDescription` — for test targeting.
- Prefer `createComposeRule()` for pure UI tests; `createAndroidComposeRule<Activity>` for Hilt.
- Isolate ViewModel by passing a fake; test logic in ViewModel unit tests.

---

## Espresso UI Tests (XML Views)

```kotlin
@RunWith(AndroidJUnit4::class)
class SettingsActivityTest {

    @get:Rule val activityRule = ActivityScenarioRule(SettingsActivity::class.java)

    @Test
    fun notificationToggle_changesState() {
        onView(withId(R.id.notificationSwitch))
            .check(matches(isDisplayed()))
            .perform(click())

        onView(withId(R.id.notificationSwitch))
            .check(matches(isChecked()))
    }
}
```

---

## Screenshot Tests — Paparazzi

```kotlin
class MediaCardPaparazziTest {

    @get:Rule val paparazzi = Paparazzi(
        deviceConfig = DeviceConfig.PIXEL_5,
        theme = "android:Theme.Material.Light.NoActionBar",
    )

    @Test
    fun media_card_default_state() {
        paparazzi.snapshot {
            MyAppTheme {
                MediaCard(item = MediaItem("1", "Song A", 180_000L, ""))
            }
        }
    }
}
```

---

## Gradle Test Dependencies

```kotlin
// build.gradle.kts (:app or :feature:*)
dependencies {
    // Unit testing
    testImplementation(libs.junit4)
    testImplementation(libs.junit5.api)
    testRuntimeOnly(libs.junit5.engine)
    testImplementation(libs.mockk)
    testImplementation(libs.turbine)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.truth)

    // Android integration tests
    androidTestImplementation(libs.androidx.test.ext.junit)
    androidTestImplementation(libs.androidx.test.espresso.core)
    androidTestImplementation(libs.hilt.android.testing)
    androidTestImplementation(libs.room.testing)

    // Compose UI tests
    androidTestImplementation(libs.compose.ui.test.junit4)
    debugImplementation(libs.compose.ui.test.manifest)

    // Screenshot tests
    testImplementation(libs.paparazzi)
}
```

---

## AOSP Test Module (Android.bp)

```soong
android_test {
    name: "MyAppTests",
    srcs: [
        "src/test/**/*.kt",
        "src/androidTest/**/*.kt",
    ],
    static_libs: [
        "junit",
        "mockk",
        "truth-prebuilt",
        "androidx.test.ext.junit",
        "androidx.test.espresso.core",
        "hilt_android_testing",
    ],
    manifest: "AndroidManifest.xml",
    certificate: "testkey",
    test_suites: ["device-tests"],
}
```

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

### Step 1: Choose the right test type
Unit tests for logic, Hilt integration tests for Jetpack components, Compose tests for UI.

### Step 2: Write the unit test
Use JUnit 4/5 + MockK; follow Arrange-Act-Assert; keep tests fast and deterministic.

### Step 3: Set up Hilt for integration tests
Annotate test class with `@HiltAndroidTest`; use `@BindValue` to replace real dependencies.

### Step 4: Write Compose UI tests
Use `createComposeRule()`; interact with `onNodeWithTag()` / `onNodeWithText()`.

### Step 5: Run and measure coverage
Execute `./gradlew testDebugUnitTest`; check the JaCoCo report; target ≥ 80% line coverage.


## Troubleshooting

- **Hilt `@HiltAndroidTest` not found** — ensure `hilt-android-testing` dependency is in `androidTestImplementation`; check `kapt hilt-android-compiler` in test deps.
- **Compose test can't find a node** — the node's `testTag` was not set; add `Modifier.testTag("id")` to the target composable.
- **Flakey test due to animation** — disable animations in test: `composeTestRule.mainClock.autoAdvance = false`; or use `AnimationTestRule`.
- **Room in-memory DB test is slow** — use `allowMainThreadQueries()` only in tests; run Room migrations in an `AndroidJUnit4` instrumented test.


## Pre-Commit Checklist

- [ ] Every new UseCase has a unit test covering success and failure paths.
- [ ] ViewModel tests use `MainDispatcherRule` and Turbine for Flow assertions.
- [ ] Room DAO tests use in-memory database.
- [ ] Hilt integration tests use `@HiltAndroidTest` and `HiltAndroidRule`.
- [ ] Compose screens have at least one UI test per interactive behaviour.
- [ ] No `Thread.sleep()` in tests — use `advanceUntilIdle()` or `awaitItem()`.
- [ ] Test class names follow `<ClassUnderTest>Test` convention.
- [ ] Mock verification (`coVerify` / `confirmVerified`) used for side-effect-producing calls.

---

## References

- [Android Testing Guide](https://developer.android.com/training/testing)
- [MockK documentation](https://mockk.io)
- [Turbine (Flow testing)](https://github.com/cashapp/turbine)
- [Compose Testing Guide](https://developer.android.com/jetpack/compose/testing)
- [Hilt Testing Guide](https://developer.android.com/training/dependency-injection/hilt-testing)
- [Paparazzi (screenshot testing)](https://github.com/cashapp/paparazzi)
