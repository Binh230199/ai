---
name: android-ndk
description: >
  Use when setting up, configuring, or reviewing Android NDK native build integration
  for C/C++ libraries in Android apps (Gradle + CMake) or AOSP modules (Soong/Android.bp).
  Covers NDK toolchain setup, CMakeLists.txt for Android, ABI selection, STL choice,
  API level targeting, and exposing native libraries to Java/Kotlin via System.loadLibrary.
argument-hint: <module-name> [setup|review|gradle|soong]
---

# Android NDK — Native Library Build Setup

Practices for integrating C/C++ native code into Android projects using the
**Android NDK**, targeting **Android Automotive OS (AAOS)** on ARM/AArch64 devices.

---

## When to Use This Skill

- Adding a new native (C/C++) library to an Android Studio (Gradle) project.
- Adding a native shared library to an AOSP module via `Android.bp`.
- Choosing the right ABI filters, API level, and C++ STL.
- Debugging "library not found" or "unsatisfied link error" at runtime.
- Setting up CMake options inside Gradle `externalNativeBuild`.

---

## Key Concepts

| Concept | Description |
|---|---|
| **ABI** | CPU architecture variant: `arm64-v8a`, `armeabi-v7a`, `x86_64`, `x86` |
| **API level** | Minimum Android API the native code targets (controls which NDK APIs are available) |
| **STL** | C++ standard library: `c++_shared` (most common), `c++_static`, `none`, `system` |
| **ndk-build** | Legacy build system (Android.mk). Use CMake for new projects. |
| **CMake** | Preferred build system for NDK native code since NDK r14 |

---

## Gradle + CMake Integration (Android Studio)

### `build.gradle.kts` (module level)

```kotlin
android {
    defaultConfig {
        externalNativeBuild {
            cmake {
                cppFlags += "-std=c++17"
                arguments += listOf(
                    "-DANDROID_STL=c++_shared",
                    "-DANDROID_ARM_NEON=TRUE"
                )
                // ABI filters — restrict to what AAOS hardware supports
                abiFilters += listOf("arm64-v8a", "armeabi-v7a")
            }
        }
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }
}
```

### `CMakeLists.txt` for Android NDK

```cmake
cmake_minimum_required(VERSION 3.22)
project(MyNativeLib VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build a shared library that Gradle packages into the APK
add_library(my_native_lib SHARED
    src/native_lib.cpp
    src/audio_processor.cpp
)

# Find NDK-provided system libraries
find_library(log-lib   log)
find_library(android-lib android)

target_link_libraries(my_native_lib
    PRIVATE
        ${log-lib}
        ${android-lib}
)

target_include_directories(my_native_lib
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)
```

### Loading the library from Kotlin/Java

```kotlin
// In a companion object or the class that calls native methods
companion object {
    init {
        System.loadLibrary("my_native_lib")
    }
}

// Declare native methods
external fun processAudio(samples: ShortArray): Int
```

---

## AOSP Soong — `Android.bp`

```
cc_library_shared {
    name: "libmy_native",
    srcs: [
        "src/native_lib.cpp",
        "src/audio_processor.cpp",
    ],
    export_include_dirs: ["include"],
    shared_libs: [
        "liblog",
        "libutils",
        "libbinder_ndk",
    ],
    cflags: ["-Wall", "-Wextra", "-Werror"],
    cppflags: ["-std=c++17"],
    // Target only 64-bit on AAOS production hardware
    compile_multilib: "64",
}

// Prebuilt .so for distribution
cc_prebuilt_library_shared {
    name: "libvendor_sensor",
    srcs: ["prebuilt/arm64-v8a/libvendor_sensor.so"],
    export_include_dirs: ["include"],
    compile_multilib: "64",
}
```

---

## ABI Selection

| ABI | Architecture | Notes |
|---|---|---|
| `arm64-v8a` | 64-bit ARMv8 | Required for all Android 11+ 64-bit-only targets (most AAOS HW) |
| `armeabi-v7a` | 32-bit ARMv7 | Legacy; needed if app runs 32-bit processes on 64-bit device |
| `x86_64` | 64-bit x86 | Android emulator / development VM |
| `x86` | 32-bit x86 | Android emulator legacy; rarely needed |

For **AAOS production targets**: filter to `arm64-v8a` only unless you explicitly need 32-bit support.

---

## C++ STL Selection

| Option | When to Use |
|---|---|
| `c++_shared` | Multiple shared libraries in the same process — all share one STL instance (avoids ODR violations) |
| `c++_static` | Single shared library with no other NDK `.so` in the process |
| `none` | Pure C code, or you provide your own STL |
| `system` | Minimal C++ runtime; **very limited** — avoid for new code |

**Rule**: If you ship more than one `.so` that uses the C++ STL, use `c++_shared` for all of them. Mixing `c++_static` across multiple `.so` files causes undefined behavior.

---

## Available NDK APIs (Selected)

The NDK exposes a stable subset of Android APIs directly to C/C++:

| Header | Provides |
|---|---|
| `<android/log.h>` | `__android_log_print` — logcat from native code |
| `<android/asset_manager.h>` | Access to `assets/` in APK |
| `<android/native_window.h>` | Native window for OpenGL ES / Vulkan surface |
| `<android/sensor.h>` | Sensor events via `ASensorManager` |
| `<android/hardware_buffer.h>` | `AHardwareBuffer` — zero-copy shared GPU buffers (API 26+) |
| `<android/binder_ibinder.h>` | Binder IPC from native code (NDK Binder, API 29+) |

Check the [NDK API reference](https://developer.android.com/ndk/reference) for the API level each symbol requires.

---

## Logging from Native Code

```cpp
#include <android/log.h>

#define LOG_TAG "MyNativeLib"
#define LOGD(...) __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,  LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

void processAudio(int sampleRate) {
    LOGI("Processing audio at %d Hz", sampleRate);
}
```

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

### Step 1: Configure CMakeLists.txt
Define `add_library(mylib SHARED ...)` with source files; set the minimum NDK API level.

### Step 2: Link to the Gradle build
Set `externalNativeBuild.cmake.path "CMakeLists.txt"` in your module's `build.gradle.kts`.

### Step 3: Set ABI filters
Use `abiFilters "arm64-v8a"` for production; add `"x86_64"` if emulator support is needed.

### Step 4: Load the library from Kotlin/Java
Call `System.loadLibrary("mylib")` in a `companion object` or static initializer block.

### Step 5: Debug native crashes
Use `ndk-stack` to symbolicate tombstone logs; attach LLDB from Android Studio for live debug.


## Troubleshooting

- **`CANNOT LINK EXECUTABLE ... not found`** — the shared library `.so` is not in the APK's `lib/<abi>/` directory; check `abiFilters` and CMake `install` rules.
- **Native crash without symbols** — add `-g` to `CMAKE_C_FLAGS` in debug builds; run `ndk-stack -sym <symbol-dir> -dump <tombstone>`.
- **STL ABI mismatch** — all libraries in the same process must use the same STL (`c++_shared`); never mix `c++_static` with `c++_shared`.
- **cmake: `NDK_ROOT` not set`** — set `ANDROID_NDK` environment variable or `android.ndkPath` in `local.properties`.


## Pre-Commit Checklist

- [ ] `abiFilters` contains only the ABIs the target hardware needs.
- [ ] `ANDROID_STL=c++_shared` if multiple native `.so` files are loaded in the same process.
- [ ] `cmake_minimum_required` version matches the version specified in `build.gradle`.
- [ ] NDK API calls checked against the minimum `minSdk` / `APP_PLATFORM` of the project.
- [ ] `find_library` used for system libs — no hardcoded lib paths.
- [ ] `LOCAL_ARM_NEON := true` (ndk-build) or `-DANDROID_ARM_NEON=TRUE` (CMake) only if code actually uses NEON intrinsics.

---

## References

- [Android NDK Guides](https://developer.android.com/ndk/guides)
- [NDK CMake Guide](https://developer.android.com/ndk/guides/cmake)
- [Android.bp reference (Soong)](https://ci.android.com/builds/submitted/latest/linux/docs.html)
- [NDK API Reference](https://developer.android.com/ndk/reference)
