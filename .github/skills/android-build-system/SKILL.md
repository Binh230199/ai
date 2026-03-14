---
name: android-build-system
description: >
  Use when configuring, reviewing, or troubleshooting Android app build files in
  either Android Studio (Gradle: Version Catalogs, Convention Plugins, KSP, build
  variants, build performance) or AOSP (Soong: Android.bp, Android.mk, module types,
  signing certificates, product packages, partition placement).
  Covers both environments for Android Automotive / AAOS projects.
argument-hint: <module-name> [gradle|soong|aosp|android.bp|version-catalog]
---

# Android Build System

Expert reference for configuring Android app builds in two environments:

1. **Android Studio / Gradle** — Kotlin DSL, Version Catalogs, Convention Plugins, KSP.
2. **AOSP / Soong** — `Android.bp`, `Android.mk`, product packages, signing, partition placement.

---

## When to Use This Skill

- Setting up a new app module in `build.gradle.kts`.
- Adding a dependency and unsure of scope (`api` vs `implementation`).
- Migrating a KAPT annotation processor to KSP.
- Creating a Convention Plugin for shared build logic.
- Writing or reviewing an `Android.bp` `android_app` module.
- Choosing signing certificate or partition for an AOSP app.
- Debugging `m`, `mma`, or Gradle sync failures.

---

## Part 1: Android Studio — Gradle (Kotlin DSL)

### Project structure

```
root/
├── build.gradle.kts                # root: only plugin repos, project-level config
├── settings.gradle.kts             # include modules, management plugins
├── gradle/
│   └── libs.versions.toml          # Version Catalog
├── build-logic/                    # Convention Plugins
│   ├── settings.gradle.kts
│   └── convention/
│       ├── build.gradle.kts
│       └── src/main/kotlin/
│           ├── AndroidApplicationConventionPlugin.kt
│           └── AndroidLibraryConventionPlugin.kt
├── app/
│   └── build.gradle.kts
└── feature/home/
    └── build.gradle.kts
```

---

### Version Catalog (`gradle/libs.versions.toml`)

```toml
[versions]
agp = "8.4.0"
kotlin = "1.9.24"
compose-bom = "2024.05.00"
hilt = "2.51"
room = "2.6.1"
retrofit = "2.11.0"
coroutines = "1.8.1"
mockk = "1.13.11"
turbine = "1.1.0"

[libraries]
# AndroidX Core
androidx-core-ktx = { group = "androidx.core", name = "core-ktx", version = "1.13.1" }
androidx-lifecycle-runtime-ktx = { group = "androidx.lifecycle", name = "lifecycle-runtime-ktx", version = "2.8.0" }

# Compose BOM (manages all compose versions via BOM)
compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "compose-bom" }
compose-ui = { group = "androidx.compose.ui", name = "ui" }
compose-material3 = { group = "androidx.compose.material3", name = "material3" }
compose-ui-test-junit4 = { group = "androidx.compose.ui", name = "ui-test-junit4" }
compose-ui-test-manifest = { group = "androidx.compose.ui", name = "ui-test-manifest" }

# Hilt
hilt-android = { group = "com.google.dagger", name = "hilt-android", version.ref = "hilt" }
hilt-compiler = { group = "com.google.dagger", name = "hilt-compiler", version.ref = "hilt" }
hilt-android-testing = { group = "com.google.dagger", name = "hilt-android-testing", version.ref = "hilt" }

# Room
room-runtime = { group = "androidx.room", name = "room-runtime", version.ref = "room" }
room-ktx = { group = "androidx.room", name = "room-ktx", version.ref = "room" }
room-compiler = { group = "androidx.room", name = "room-compiler", version.ref = "room" }

# Network
retrofit = { group = "com.squareup.retrofit2", name = "retrofit", version.ref = "retrofit" }
okhttp-logging = { group = "com.squareup.okhttp3", name = "logging-interceptor", version = "4.12.0" }

# Testing
junit4 = { group = "junit", name = "junit", version = "4.13.2" }
mockk = { group = "io.mockk", name = "mockk", version.ref = "mockk" }
turbine = { group = "app.cash.turbine", name = "turbine", version.ref = "turbine" }
kotlinx-coroutines-test = { group = "org.jetbrains.kotlinx", name = "kotlinx-coroutines-test", version.ref = "coroutines" }
truth = { group = "com.google.truth", name = "truth", version = "1.4.2" }

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
android-library = { id = "com.android.library", version.ref = "agp" }
kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
hilt = { id = "com.google.dagger.hilt.android", version.ref = "hilt" }
ksp = { id = "com.google.devtools.ksp", version = "1.9.24-1.0.20" }
room = { id = "androidx.room", version.ref = "room" }

[bundles]
compose = ["compose-ui", "compose-material3", "androidx-lifecycle-runtime-ktx"]
testing-unit = ["junit4", "mockk", "turbine", "kotlinx-coroutines-test", "truth"]
```

---

### Convention Plugins

Convention Plugins centralise shared build logic in `build-logic/`.
Each feature module adds a single plugin instead of duplicating config.

```kotlin
// build-logic/convention/src/main/kotlin/AndroidApplicationConventionPlugin.kt
class AndroidApplicationConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.android.application")
                apply("org.jetbrains.kotlin.android")
                apply("com.google.dagger.hilt.android")
                apply("com.google.devtools.ksp")
            }
            extensions.configure<ApplicationExtension> {
                configureKotlinAndroid(this)
                defaultConfig.targetSdk = 34
            }
        }
    }
}

// Shared AndroidOptions extension
internal fun Project.configureKotlinAndroid(commonExtension: CommonExtension<*, *, *, *, *, *>) {
    commonExtension.apply {
        compileSdk = 34
        defaultConfig { minSdk = 30 }
        compileOptions {
            sourceCompatibility = JavaVersion.VERSION_17
            targetCompatibility = JavaVersion.VERSION_17
        }
        kotlinOptions { jvmTarget = "17" }
    }
}
```

```kotlin
// build-logic/convention/build.gradle.kts
plugins { `kotlin-dsl` }
dependencies {
    compileOnly(libs.agp)
    compileOnly(libs.kotlin.gradle.plugin)
}
gradlePlugin {
    plugins {
        register("androidApplication") {
            id = "myapp.android.application"
            implementationClass = "AndroidApplicationConventionPlugin"
        }
    }
}
```

```kotlin
// app/build.gradle.kts — minimal!
plugins {
    alias(libs.plugins.myapp.android.application)  // convention plugin
}
android {
    namespace = "com.example.myapp"
    defaultConfig { applicationId = "com.example.myapp" }
    signingConfigs { ... }
}
dependencies {
    implementation(project(":feature:home"))
    implementation(libs.bundles.compose)
    ksp(libs.hilt.compiler)
}
```

---

### Dependency Scopes

| Scope | When to Use |
|---|---|
| `implementation` | Internal dependency; not exposed to consumers |
| `api` | Dependency exposed as part of module's public API |
| `compileOnly` | Needed at compile time only (annotations, generated code) |
| `runtimeOnly` | Needed at runtime only (JDBC drivers, logging impls) |
| `testImplementation` | Unit tests only (JVM) |
| `androidTestImplementation` | Instrumented tests (device/emulator) |
| `debugImplementation` | Debug builds only (LeakCanary, Compose test manifest) |
| `ksp` | KSP annotation processor (Room, Hilt) |

**Rules**
- Prefer `implementation` over `api` — leaking transitive dependencies causes slow builds.
- Use `ksp` instead of `kapt` for all new annotation processors.
- Use Compose BOM — do not specify Compose library versions individually.

---

### Build Variants

```kotlin
android {
    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            isDebuggable = true
            isMinifyEnabled = false
        }
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    productFlavors {
        flavorDimensions += "target"
        create("phone") { dimension = "target" }
        create("automotive") {
            dimension = "target"
            applicationIdSuffix = ".auto"
        }
    }
}
```

---

### Build Performance

```kotlin
// gradle.properties
org.gradle.configuration-cache=true        # cache task graph between builds
org.gradle.caching=true                    # reuse task outputs from cache
org.gradle.parallel=true                   # parallel module compilation
org.gradle.daemon=true                     # keep Gradle in memory
kotlin.incremental=true
android.enableR8.fullMode=true             # better shrinking
```

- Use `ksp` (not `kapt`) — 2× faster annotation processing.
- Keep `:core:*` modules small and stable — they are on the critical compilation path.
- Avoid `api` dependencies — transitive dependency changes force consumer recompilation.

---

## Part 2: AOSP — Soong Build System (Android.bp)

### android_app module

```soong
android_app {
    name: "MyCarApp",

    // Source
    srcs: ["src/**/*.kt", "src/**/*.java"],
    resource_dirs: ["res"],
    asset_dirs: ["assets"],
    manifest: "AndroidManifest.xml",

    // Dependencies
    static_libs: [
        // Jetpack (bundled in AOSP)
        "androidx.appcompat_appcompat",
        "androidx.lifecycle_lifecycle-viewmodel-ktx",
        "androidx.navigation_navigation-fragment-ktx",
        "car-ui-lib",
        "hilt_android",
    ],
    libs: [
        "android.car",         // platform lib — link only, not bundled
    ],

    // Build config
    sdk_version: "current",        // prefer over platform_apis
    min_sdk_version: "30",
    target_sdk_version: "34",

    // Signing & placement
    certificate: "platform",       // platform, shared, media, testkey
    privileged: true,              // /system/priv-app
    product_specific: true,        // /product/priv-app (if product_specific + privileged)

    // Kotlin
    kotlincflags: ["-Xjvm-default=all"],

    // Annotation processors
    plugins: ["hilt_compiler"],

    // Optimization
    dex_preopt: { enabled: true, profile: "profile.txt" },

    // Lint
    lint: { strict: ["NewApi"], warning: ["MissingPermission"] },
}
```

### android_library module

```soong
android_library {
    name: "MyCarLib",
    srcs: ["src/**/*.kt"],
    resource_dirs: ["res"],
    manifest: "AndroidManifest.xml",
    static_libs: ["androidx.core_core-ktx"],
    sdk_version: "current",
    apex_available: ["//apex_available:platform"],
}
```

### java_library (pure Kotlin/Java, no Android)

```soong
java_library {
    name: "MyDomainLib",
    srcs: ["src/**/*.kt"],
    sdk_version: "current",
    libs: ["kotlin-stdlib"],
}
```

---

### Signing Certificates

| Certificate | Key location | Use when |
|---|---|---|
| `testkey` | `build/target/product/security/testkey` | Development / test builds |
| `platform` | `build/target/product/security/platform` | System/privileged apps sharing platform UID |
| `shared` | `build/target/product/security/shared` | Apps sharing `SharedUserId` with contacts/phone |
| `media` | `build/target/product/security/media` | Media provider apps |
| `"vendor/..."` | Custom OEM key path | Production OEM signing |

**Rules**
- Never use `testkey` in production flash images.
- `platform` certificate allows sharing UID with system — only when strictly needed.
- For custom OEM certificates: `certificate: "vendor/oem/certs/mykey"`.

---

### Partition Placement

| Android.bp property | Partition | Path |
|---|---|---|
| default | System | `/system/app` |
| `privileged: true` | System (priv) | `/system/priv-app` |
| `product_specific: true` | Product | `/product/app` |
| `product_specific: true` + `privileged: true` | Product (priv) | `/product/priv-app` |
| `vendor: true` | Vendor | `/vendor/app` |
| `soc_specific: true` | SoC | `/odm/app` |

---

### Product Package Inclusion

```makefile
# device/oem/product/my_product.mk
PRODUCT_PACKAGES += \
    MyCarApp \
    MyCarLib
```

---

### Legacy Android.mk (read-only reference)

```makefile
LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE_TAGS := optional
LOCAL_PACKAGE_NAME := MyCarApp
LOCAL_SRC_FILES := $(call all-subdir-java-files)
LOCAL_RESOURCE_DIR := $(LOCAL_PATH)/res
LOCAL_MANIFEST_FILE := AndroidManifest.xml

LOCAL_STATIC_JAVA_LIBRARIES := \
    androidx.appcompat_appcompat \
    car-ui-lib

LOCAL_JAVA_LIBRARIES := android.car

LOCAL_CERTIFICATE := platform
LOCAL_PRIVILEGED_MODULE := true
LOCAL_PRODUCT_MODULE := true

include $(BUILD_PACKAGE)
```

**Rule**: Prefer `Android.bp` (Soong) for all new modules. `Android.mk` is legacy and
not supported in Bazel/Soong hybrid builds.

---

### Common AOSP Build Commands

```bash
# Initialize build environment
source build/envsetup.sh
lunch <product>-<variant>       # e.g., aosp_car_x86_64-userdebug

# Build specific module
m MyCarApp                      # build + place in out/
mma                             # build current dir + dependencies
mmm packages/apps/MyCarApp      # build specific directory

# Install to running device
adb install out/target/product/<product>/product/priv-app/MyCarApp/MyCarApp.apk
# or
adb sync product                # sync entire product partition

# Check installed module
adb shell pm list packages -f | grep MyCarApp
```

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

### Step 1: Identify the build environment
Determine whether you are working in Android Studio (Gradle) or AOSP (Soong / Android.bp).

### Step 2: Configure dependencies / modules
Add dependencies in `build.gradle.kts` (Gradle) or `Android.bp` (Soong).

### Step 3: Define build variants or module types
Set up `buildTypes` and `productFlavors` (Gradle) or `cc_library` / `android_app` (Soong).

### Step 4: Build and resolve errors
Run `./gradlew assembleDebug` (Gradle) or `m <module>` (AOSP); fix any reported errors.

### Step 5: Sign and package for release
Configure signing configs (Gradle) or `certificate` field (Soong) for release builds.


## Troubleshooting

- **`Duplicate class` Gradle error** — conflicting transitive dependency versions; use `implementation(enforcedPlatform(...))` or `resolutionStrategy.force`.
- **AOSP `ninja: error: ...` during `m`** — check `Android.bp` syntax with `bpfmt -w Android.bp`; look for circular dependencies.
- **Gradle build cache miss slowing CI** — enable `org.gradle.caching=true` in `gradle.properties`; configure a remote build cache.
- **APK not signed for release** — configure `signingConfigs` in `build.gradle.kts` and reference it in the `release` build type.


## Pre-Commit Checklist

### Gradle
- [ ] New dependencies use Version Catalog aliases, not string literals.
- [ ] Scope is `implementation`, not `api`, unless intentionally exposing the API.
- [ ] KSP used for annotation processors, not KAPT.
- [ ] Convention Plugin used for shared build config, not copy-pasted blocks.
- [ ] Configuration Cache enabled and not broken by the change.

### AOSP Soong
- [ ] `Android.bp` module name is PascalCase and unique in the product.
- [ ] Correct `sdk_version` — prefer `"current"` over `platform_apis: true`.
- [ ] `certificate` matches security requirements (dev vs release).
- [ ] Partition (`privileged`, `product_specific`, `vendor`) is intentional.
- [ ] `PRODUCT_PACKAGES` updated in product `.mk` file.
- [ ] App builds and installs with `m MyModule ; adb sync`.

---

## References

- [Gradle Kotlin DSL](https://docs.gradle.org/current/userguide/kotlin_dsl.html)
- [Android Gradle Plugin docs](https://developer.android.com/build/releases/gradle-plugin)
- [Version Catalogs](https://docs.gradle.org/current/userguide/platforms.html)
- [Soong Build System (AOSP)](https://source.android.com/docs/setup/build/building)
- [Android.bp Reference](https://ci.android.com/builds/submitted/latest/linux/docs/soong_build.html)
- [Now in Android — build-logic](https://github.com/android/nowinandroid/tree/main/build-logic)
