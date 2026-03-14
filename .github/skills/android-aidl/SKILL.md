---
name: android-aidl
description: >
  Use when writing, reviewing, or debugging AIDL (Android Interface Definition
  Language) interface files for IPC between Android processes. Covers .aidl syntax,
  primitive and Parcelable types, oneway modifier, directional parameters, versioning
  and stability, and generating Java/C++ binder stubs in Gradle and AOSP Soong builds.
argument-hint: <interface-name> [write|review|debug]
---

# Android AIDL — Interface Definition Language

Practices for defining correct, versioned AIDL interfaces for use in Android
applications and HAL services targeting **Android Automotive OS (AAOS)**.

Source of truth: [Android AIDL Guide](https://developer.android.com/guide/components/aidl)
and [AIDL Backends](https://source.android.com/docs/core/architecture/aidl/aidl-backends).

---

## When to Use This Skill

- Defining IPC interfaces between apps or between an app and a bound `Service`.
- Defining HAL interfaces (AIDL HAL, Android 11+) in AOSP.
- Passing custom data types across process boundaries (Parcelable).
- Controlling one-way (async) vs. two-way (blocking) calls.

---

## Basic AIDL Interface

```aidl
// IRemoteCounter.aidl — saved under a package directory
package com.example.counter;

// Interfaces extend nothing (no extends syntax in AIDL)
interface IRemoteCounter {
    void reset();
    int getCount();
    void increment(int delta);
    String getTag();
}
```

Generated stub/proxy:
- **Gradle**: Java stubs placed in `build/generated/`.
- **AOSP Soong**: NDK/CPP/Java stubs generated from a `filegroup` → `aidl_interface`.

---

## Supported AIDL Types

| Category | Types |
|---|---|
| Primitives | `boolean`, `byte`, `char`, `int`, `long`, `float`, `double` |
| String | `String` (always `in` direction) |
| Arrays | `int[]`, `byte[]`, etc. |
| List | `List` (contents must be in the set of AIDL-supported types) |
| Parcelable | any `parcelable` declared in AIDL |
| Interface | any `interface` declared in AIDL (passed as `IBinder`) |
| `FileDescriptor` | for passing file descriptors cross-process |

---

## Parcelable — Custom Data Types

```aidl
// SensorData.aidl
package com.example.sensor;

parcelable SensorData {
    int sensorId;
    float value;
    long timestampNs;
    String unit;
}
```

Java side: if you generate Java stubs, the parcelable fields are accessible directly.

C++ (NDK backend) side: the generated class has `Parcel::readFromParcel` and `writeToParcel`.

For hand-written Java implementation of a Parcelable, you write a separate `.java` file implementing `android.os.Parcelable` — the `.aidl` file is then just the declaration.

---

## Directional Parameters

For non-primitive parameters, you must declare the data flow direction:

| Direction | Meaning | Usage |
|---|---|---|
| `in` | Caller → Callee (read-only for callee) | Most inputs |
| `out` | Callee fills the buffer (write-only for callee, caller provides pre-allocated object) | Output buffers |
| `inout` | Both directions — data sent in, modified, sent back | Read-modify-write |

```aidl
interface IProcessor {
    void process(in SensorData input, out ResultData result);
    void update(inout ConfigData config);
}
```

Primitives and `String` are always `in`. You may omit the direction keyword for `in`-only primitives.

---

## The `oneway` Modifier

`oneway` makes a method call asynchronous — the caller does not block and the method cannot return a value or throw.

```aidl
interface IEventListener {
    oneway void onSensorEvent(in SensorData event);
    oneway void onError(int code, String message);
}
```

**Rules:**
- `oneway` methods cannot have return values (must be `void`).
- `oneway` methods cannot have `out` or `inout` parameters.
- You can mark the entire interface as `oneway`: `oneway interface IListener { ... }`.
- Calls are queued and delivered in-order per interface.

---

## Versioning and Stability (`@VintfStability` / frozen versions)

For interfaces shared across processes with different update schedules (e.g., HAL services), use versioned `aidl_interface` in AOSP:

```
// hardware/interfaces/audio/IMyAudioHal.aidl
package android.hardware.audio;  // use android.hardware.* namespace for HALs

@VintfStability
interface IMyAudioHal {
    void start();
    void stop();
    int getVolume();
}
```

- `@VintfStability` marks the interface as part of the VINTF surface — it must be frozen before shipping.
- Frozen interfaces can only be extended (new methods), never changed or removed.
- Versioning uses `aidl_interface` with `versions:` in `Android.bp`.

---

## AOSP Soong Build (Android.bp)

```soong
aidl_interface {
    name: "my-audio-hal-aidl",
    srcs: ["hardware/interfaces/audio/*.aidl"],
    stability: "vintf",
    backend: {
        cpp: { enabled: true },
        ndk: { enabled: true },
        java: { enabled: false },
    },
    versions: ["1"],  // frozen version list
}
```

- `stability: "vintf"` → equivalent to `@VintfStability` on all interfaces.
- `backend.ndk` → generates NDK-compatible C++ stubs usable from native code.
- `backend.cpp` → generates libbinder-level stubs for system/HAL C++ code.
- Source library dependency: `"my-audio-hal-aidl-ndk"` or `"my-audio-hal-aidl-cpp"`.

---

## Gradle Build (Android Studio projects)

```
src/
  main/
    aidl/
      com/example/counter/
        IRemoteCounter.aidl
    java/
      com/example/counter/
        RemoteCounterService.java
```

In `build.gradle` (Groovy) or `build.gradle.kts` (Kotlin DSL):
```groovy
android {
    buildFeatures {
        aidl = true
    }
}
```

Stubs are generated automatically and placed in `build/generated/aidl_source_output_dir/`.

---

## Implementing an AIDL Service (Java)

```java
public class RemoteCounterService extends Service {

    private final IRemoteCounter.Stub mBinder = new IRemoteCounter.Stub() {
        private int mCount = 0;

        @Override
        public synchronized void reset() {
            mCount = 0;
        }

        @Override
        public synchronized int getCount() {
            return mCount;
        }

        @Override
        public synchronized void increment(int delta) {
            mCount += delta;
        }

        @Override
        public String getTag() {
            return "counter";
        }
    };

    @Override
    public IBinder onBind(Intent intent) {
        return mBinder;
    }
}
```

---

## Implementing an AIDL Service (C++ / NDK backend)

```cpp
#include <aidl/com/example/counter/BnRemoteCounter.h>  // generated Bn stub

using aidl::com::example::counter::BnRemoteCounter;

class RemoteCounterImpl : public BnRemoteCounter {
public:
    ndk::ScopedAStatus reset() override {
        std::lock_guard<std::mutex> lock(mutex_);
        count_ = 0;
        return ndk::ScopedAStatus::ok();
    }

    ndk::ScopedAStatus getCount(int32_t* _aidl_return) override {
        std::lock_guard<std::mutex> lock(mutex_);
        *_aidl_return = count_;
        return ndk::ScopedAStatus::ok();
    }

    ndk::ScopedAStatus increment(int32_t delta) override {
        std::lock_guard<std::mutex> lock(mutex_);
        count_ += delta;
        return ndk::ScopedAStatus::ok();
    }

    ndk::ScopedAStatus getTag(std::string* _aidl_return) override {
        *_aidl_return = "counter";
        return ndk::ScopedAStatus::ok();
    }

private:
    std::mutex mutex_;
    int32_t count_ = 0;
};
```

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

### Step 1: Define the AIDL interface
Create the `.aidl` file with the correct package declaration and method signatures.
Follow the Basic AIDL Syntax and Supported AIDL Types sections below.

### Step 2: Configure the build
Add the `.aidl` file to the Gradle `sourceSets` or AOSP `Android.bp` module.

### Step 3: Implement the Binder stub
Generate and implement the `Stub` class in the service process.

### Step 4: Bind the service (client side)
Implement `ServiceConnection` and cast the `IBinder` to the AIDL interface.

### Step 5: Add versioning (if needed)
Define `const int VERSION` in the AIDL and implement `getInterfaceVersion()`.


## Troubleshooting

- **`cannot find symbol` for AIDL-generated class** — clean and rebuild; check `sourceSets.main.aidl.srcDirs` in Gradle.
- **`SecurityException` when binding** — the client is missing the `android.permission.*` declared by the service; add the permission to the client manifest.
- **`android.os.DeadObjectException`** — the service process died; implement `IBinder.DeathRecipient` to reconnect.
- **AIDL version mismatch** — ensure both client and server compile against the same AIDL interface version; use `getInterfaceVersion()` for defensive checks.


## Pre-Commit Checklist

- [ ] All `.aidl` files placed under the correct package directory.
- [ ] Directional tags (`in`/`out`/`inout`) on all non-primitive parameters.
- [ ] `oneway` methods are `void` with no `out`/`inout` params.
- [ ] `@VintfStability` present on interfaces shared across VINTF boundary.
- [ ] HAL interfaces use `android.hardware.*` package namespace.
- [ ] Frozen versions listed in `Android.bp` `versions:` before release.
- [ ] No methods removed or signatures changed in frozen interface versions.

---

## References

- [AIDL Overview](https://developer.android.com/guide/components/aidl)
- [AIDL for HALs (AOSP)](https://source.android.com/docs/core/architecture/aidl)
- [AIDL Backends](https://source.android.com/docs/core/architecture/aidl/aidl-backends)
- [AIDL Stability](https://source.android.com/docs/core/architecture/aidl/stability)
