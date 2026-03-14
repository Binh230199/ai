---
name: android-app-development
description: >
  Use when writing, reviewing, or scaffolding Android application components
  (Activity, Fragment, Service, BroadcastReceiver, ContentProvider) in either
  Android Studio (Gradle) or AOSP (Soong) build environments.
  Covers Android lifecycle, Intents, Permissions, AndroidManifest, Navigation,
  and app-level architecture conventions for Android Automotive / AAOS targets.
argument-hint: <component-or-feature-name> [write|review|debug]
---

# Android App Development

Expert practices for building production-quality Android applications targeting
**Android Automotive OS (AAOS)** IVI and RSE units, applicable equally in an
**Android Studio / Gradle** project and in an **AOSP source tree (Soong)**.

Standards baseline: **Android API 33** (default minimum) · Kotlin primary, Java allowed for legacy.

---

## When to Use This Skill

- Creating or reviewing an Activity, Fragment, Service, BroadcastReceiver, or ContentProvider.
- Designing or debugging app lifecycle transitions (resume/pause/stop/destroy).
- Configuring `AndroidManifest.xml` — permissions, components, intent filters.
- Implementing runtime permission requests and rationale flows.
- Setting up Navigation Component (NavController, NavGraph, destinations).
- Integrating an app into an AOSP product (`Android.bp`, product packages, signing).

---

## Prerequisites

- Kotlin or Java (project-specific).
- Android Jetpack (lifecycle, navigation-fragment, activity-ktx).
- Hilt for dependency injection (see `android-architecture` skill).
- Build environment identified: Android Studio (Gradle) **or** AOSP (Soong).

---

## Core Android Components

### Activity

```kotlin
@AndroidEntryPoint // Hilt
class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)
        // or: setContent { MyTheme { NavHost(...) } }  // Compose entry
    }
}
```

**Rules**
- Use `AppCompatActivity` (or `ComponentActivity` for Compose-only screens).
- Never retain references to `View` or `Activity` context in a ViewModel.
- Use `registerForActivityResult` instead of deprecated `onActivityResult`.
- Persist transient state with `onSaveInstanceState`; use ViewModel for config-change state.

### Fragment

```kotlin
@AndroidEntryPoint
class DashboardFragment : Fragment(R.layout.fragment_dashboard) {

    private val viewModel: DashboardViewModel by viewModels()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { render(it) }
            }
        }
    }
}
```

**Rules**
- Always use `viewLifecycleOwner` (not `this`) when observing LiveData or StateFlow.
- Avoid Fragment-to-Fragment direct dependencies — communicate via shared ViewModel or NavController.
- Prefer `by viewModels()` / `by activityViewModels()` over manual `ViewModelProvider`.

### Service

| Type | Base Class | Use Case |
|---|---|---|
| Foreground | `Service` + `startForeground()` | Media playback, navigation |
| Background (bounded) | `Service` + `onBind()` | IPC to other components |
| Intent-based | `JobIntentService` / `WorkManager` | Deferrable, guaranteed work |

```kotlin
class MediaPlaybackService : Service() {
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIFICATION_ID, buildNotification())
        return START_STICKY
    }
    override fun onBind(intent: Intent): IBinder? = null
}
```

**Rule**: Always stop or re-bind orphaned services. In AAOS, foreground services
that play audio must use a `MediaSession`.

### BroadcastReceiver

```kotlin
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            // launch WorkManager jobs, not long-running tasks
        }
    }
}
```

**Rules**
- For sensitive broadcasts, register in manifest with `android:exported="false"` or appropriate permission.
- Never do long-running work in `onReceive` — delegate to WorkManager or a coroutine service.

---

## AndroidManifest.xml

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <!-- Permissions -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />

    <application
        android:name=".MyApplication"
        android:label="@string/app_name"
        android:theme="@style/Theme.MyApp"
        android:networkSecurityConfig="@xml/network_security_config">

        <activity
            android:name=".ui.main.MainActivity"
            android:exported="true"
            android:launchMode="singleTask">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <!-- Automotive: opt-in to system UI templates -->
        <meta-data
            android:name="com.android.automotive"
            android:resource="@xml/automotive_app_desc" />

    </application>
</manifest>
```

**Rules**
- Always set `android:exported` explicitly (required Android 12+).
- Network security config must block `http://` in production builds.
- Automotive apps must include `automotive_app_desc.xml`.

---

## Permissions

### Runtime permission request (Kotlin)

```kotlin
private val requestPermissionLauncher =
    registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { permissions ->
        val granted = permissions.entries.all { it.value }
        if (!granted) showPermissionRationale()
    }

fun requestMediaPermissions() {
    val permissions = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        arrayOf(Manifest.permission.READ_MEDIA_IMAGES, Manifest.permission.READ_MEDIA_VIDEO)
    } else {
        arrayOf(Manifest.permission.READ_EXTERNAL_STORAGE)
    }
    requestPermissionLauncher.launch(permissions)
}
```

**Rules**
- Check `shouldShowRequestPermissionRationale()` before re-request.
- Never request permissions at app start without user-initiated action context.
- AAOS: some `android.car.*` permissions are `signatureOrSystem` — only available to privileged apps.

---

## Navigation Component

```kotlin
// NavGraph definition (nav_graph.xml)
<navigation app:startDestination="@id/homeFragment">
    <fragment android:id="@+id/homeFragment" android:name=".ui.home.HomeFragment">
        <action android:id="@+id/to_detail" app:destination="@id/detailFragment" />
    </fragment>
    <fragment android:id="@+id/detailFragment" android:name=".ui.detail.DetailFragment">
        <argument android:name="itemId" app:argType="string" />
    </fragment>
</navigation>
```

```kotlin
// Navigate
findNavController().navigate(HomeFragmentDirections.toDetail(itemId = id))

// Back
findNavController().navigateUp()
```

**Rules**
- Use Safe Args plugin for type-safe navigation arguments.
- Deep links: declare in manifest AND nav graph.
- Avoid calling `navigate()` in a `Flow` collect without checking `currentDestination`.

---

## AOSP Integration

### Android.bp — `android_app` module

```soong
android_app {
    name: "MyCarApp",
    srcs: ["src/**/*.kt", "src/**/*.java"],
    resource_dirs: ["res"],
    manifest: "AndroidManifest.xml",

    // Dependencies
    static_libs: [
        "androidx.lifecycle_lifecycle-viewmodel-ktx",
        "androidx.navigation_navigation-fragment-ktx",
        "car-ui-lib",
    ],
    libs: [
        "android.car",
    ],

    // Build config
    sdk_version: "current",          // or "33" for specific API
    min_sdk_version: "30",
    target_sdk_version: "33",

    // App characteristics
    privileged: true,                // place in /system/priv-app
    certificate: "platform",         // or "shared", "media", "testkey"
    product_specific: true,          // place in /product/priv-app

    // Optimization
    dex_preopt: {
        enabled: false,              // disable for faster build iterations
    },
}
```

### Product package inclusion

```makefile
# device.mk or product.mk
PRODUCT_PACKAGES += \
    MyCarApp
```

### Key properties

| Property | Effect |
|---|---|
| `privileged: true` | /system/priv-app — can request `signatureOrSystem` permissions |
| `platform_apis: true` | access hidden platform APIs (use sparingly) |
| `certificate: "platform"` | signed with platform key — can share UID with system |
| `product_specific: true` | placed in /product partition |
| `vendor_specific: true` | placed in /vendor partition |

**Rules**
- Prefer `sdk_version: "current"` over `platform_apis: true`.
- Use `platform_apis: true` only when a hidden API is unavoidable and documented via `@hide` in AOSP source.
- Always verify with `adb shell pm list packages -f | grep MyCarApp` after flashing.

---

## Lifecycle State Machine

```
Created → Started → Resumed (visible + focused)
          ↑               |
          └───── Paused ──┘
                    |
                  Stopped
                    |
                 Destroyed
```

**Rules**
- Start/stop animations, sensors, camera in `onResume`/`onPause`.
- Release heavy resources in `onStop`; restore in `onStart`.
- Observe `Flow` inside `repeatOnLifecycle(Lifecycle.State.STARTED)` to stop collection when app goes background.

---

## Step-by-Step Workflows

### Step 1: Define the component
Identify whether you need Activity, Fragment, Service, BroadcastReceiver, or ContentProvider.

### Step 2: Register in AndroidManifest.xml
Add the component declaration with the correct `intent-filter` and permissions.

### Step 3: Implement the lifecycle methods
Override only the callbacks you need; always delegate to `super` for others.

### Step 4: Connect to ViewModel or Service
Use `ViewModelProvider` for UI logic; bind/start Services for background work.

### Step 5: Test the component
Write unit tests for ViewModel logic and instrumented tests for the component lifecycle.


## Troubleshooting

- **Activity not launched / `ActivityNotFoundException`** — verify `intent-filter` in `AndroidManifest.xml`; check action string and category.
- **`java.lang.IllegalStateException: Can not perform this action after onSaveInstanceState`** — use `commitAllowingStateLoss()` only as a last resort; properly guard fragment transactions by lifecycle state.
- **Memory leak via static Context** — never store `Activity` or `View` in static fields; use `ApplicationContext` for long-lived components.
- **Service killed by system** — call `startForeground()` for long-running services; handle `onTaskRemoved()` for cleanup.


## Pre-Commit Checklist

- [ ] No hardcoded strings — all in `res/values/strings.xml`.
- [ ] `android:exported` explicitly set on all manifest components.
- [ ] No `Context` stored in non-context-aware classes.
- [ ] Runtime permissions checked before accessing protected resources.
- [ ] Navigation: back stack managed — no duplicate destinations accumulation.
- [ ] AOSP: `Android.bp` certificate and partition placement verified.
- [ ] No `System.out.println` or bare `Log.d` without tag constant.

---

## References

- [Android App Architecture Guide](https://developer.android.com/topic/architecture)
- [Navigation Component Docs](https://developer.android.com/guide/navigation)
- [AOSP — Building Apps](https://source.android.com/docs/setup/build/building)
- [Android.bp Reference](https://ci.android.com/builds/submitted/latest/linux/docs/soong_build.html)
