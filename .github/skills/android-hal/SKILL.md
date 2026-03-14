---
name: android-hal
description: >
  Use when implementing, registering, or debugging Android Hardware Abstraction
  Layer (HAL) services. Covers AIDL HAL (current standard, Android 11+):
  implementing the AIDL stub in C++, registering with ServiceManager, writing
  init.rc service declarations, and VINTF manifest entries. Includes a brief note
  on HIDL as a legacy approach for Android 8–10.
argument-hint: <hal-name> [implement|register|debug]
---

# Android HAL — Hardware Abstraction Layer

Practices for implementing HAL services for **Android Automotive OS (AAOS)**
using **AIDL HAL (Android 11+)** as the current standard.

Source of truth:
- [Implementing an AIDL HAL](https://source.android.com/docs/core/architecture/aidl/aidl-hals)
- [VINTF Overview](https://source.android.com/docs/core/architecture/vintf)

---

## When to Use This Skill

- Implementing an AIDL HAL stub in C++ for an AOSP platform service.
- Registering a HAL service with `ServiceManager` and writing `init.rc` entries.
- Adding VINTF manifest fragments for a new HAL interface.
- Debugging HAL connectivity issues (service not found, AIDL version mismatch).
- Migrating a legacy HIDL HAL to AIDL HAL.

---

## AIDL HAL vs. HIDL

| | AIDL HAL (current) | HIDL (legacy) |
|---|---|---|
| Introduced | Android 11 | Android 8 |
| Interface format | `.aidl` | `.hal` |
| IPC transport | Binder (same as apps) | HwBinder (separate domain) |
| Code generation | `aidl_interface` with `stability: "vintf"` | `hidl-gen` |
| Status | **Preferred for all new HALs** | Deprecated — migrate to AIDL HAL |

For new development, always use **AIDL HAL**. HIDL is maintained for compatibility with Android 8–10 products only.

---

## AIDL HAL File Structure

```
hardware/interfaces/
  myhardware/
    IMySensor.aidl          // interface definition
    MySensorData.aidl       // parcelable data type
    Android.bp              // aidl_interface build rule
  myhardware/default/
    MySensorService.h       // BnMySensor implementation header
    MySensorService.cpp     // implementation
    service.cpp             // main() — registers and waits
    Android.bp              // cc_binary build rule
    android.hardware.myhardware-default.rc  // init.rc for the service
    android.hardware.myhardware-default.xml // VINTF manifest fragment
```

---

## Step 1 — Define the AIDL Interface

```aidl
// hardware/interfaces/myhardware/IMySensor.aidl
package android.hardware.myhardware;

@VintfStability
interface IMySensor {
    float readTemperature();
    void calibrate(float offset);
    oneway void registerCallback(in IMyCallback callback);
}
```

```soong
// hardware/interfaces/myhardware/Android.bp
aidl_interface {
    name: "android.hardware.myhardware",
    srcs: ["*.aidl"],
    stability: "vintf",
    backend: {
        cpp: { enabled: false },
        ndk: { enabled: true },  // NDK backend for native HAL implementation
        java: { enabled: false },
    },
    versions: ["1"],
}
```

---

## Step 2 — Implement the AIDL Stub in C++

```cpp
// MySensorService.h
#pragma once
#include <aidl/android/hardware/myhardware/BnMySensor.h>

namespace aidl::android::hardware::myhardware {

class MySensorService : public BnMySensor {
public:
    ndk::ScopedAStatus readTemperature(float* _aidl_return) override;
    ndk::ScopedAStatus calibrate(float offset) override;
    ndk::ScopedAStatus registerCallback(
        const std::shared_ptr<IMyCallback>& callback) override;
};

}  // namespace aidl::android::hardware::myhardware
```

```cpp
// MySensorService.cpp
#include "MySensorService.h"
#include <android/log.h>

namespace aidl::android::hardware::myhardware {

ndk::ScopedAStatus MySensorService::readTemperature(float* _aidl_return) {
    // Read from hardware
    *_aidl_return = readFromHardware();
    return ndk::ScopedAStatus::ok();
}

ndk::ScopedAStatus MySensorService::calibrate(float offset) {
    applyCalibrationOffset(offset);
    return ndk::ScopedAStatus::ok();
}

ndk::ScopedAStatus MySensorService::registerCallback(
    const std::shared_ptr<IMyCallback>& callback) {
    std::lock_guard<std::mutex> lock(callbackMutex_);
    callback_ = callback;
    return ndk::ScopedAStatus::ok();
}

}  // namespace aidl::android::hardware::myhardware
```

---

## Step 3 — Register the Service with ServiceManager

```cpp
// service.cpp — the HAL process entry point
#include "MySensorService.h"
#include <android/binder_manager.h>
#include <android/binder_process.h>

using aidl::android::hardware::myhardware::MySensorService;

int main() {
    ABinderProcess_setThreadPoolMaxThreadCount(0);  // binder thread pool

    auto service = ndk::SharedRefBase::make<MySensorService>();

    // Instance name: "<interface>/<instance>" — "default" is conventional
    const std::string instanceName =
        std::string(MySensorService::descriptor) + "/default";

    binder_status_t status =
        AServiceManager_addService(service->asBinder().get(), instanceName.c_str());

    if (status != STATUS_OK) {
        ALOGE("Failed to register %s: %d", instanceName.c_str(), status);
        return EXIT_FAILURE;
    }

    ABinderProcess_joinThreadPool();
    return EXIT_SUCCESS;  // unreachable
}
```

```soong
// hardware/interfaces/myhardware/default/Android.bp
cc_binary {
    name: "android.hardware.myhardware-service.default",
    relative_install_path: "hw",
    init_rc: ["android.hardware.myhardware-default.rc"],
    vintf_fragments: ["android.hardware.myhardware-default.xml"],
    srcs: [
        "service.cpp",
        "MySensorService.cpp",
    ],
    shared_libs: [
        "libbase",
        "libbinder_ndk",
        "android.hardware.myhardware-V1-ndk",
    ],
    vendor: true,
}
```

---

## Step 4 — init.rc Service Declaration

```rc
# android.hardware.myhardware-default.rc
service vendor.myhardware-default /vendor/bin/hw/android.hardware.myhardware-service.default
    class hal
    user system
    group system
    shutdown critical
```

**Common class values**: `hal` (standard HAL services), `core`, `main`.

---

## Step 5 — VINTF Manifest Fragment

Declare the HAL in the VINTF manifest so the framework knows the HAL is available:

```xml
<!-- android.hardware.myhardware-default.xml -->
<manifest version="1.0" type="device">
    <hal format="aidl">
        <name>android.hardware.myhardware</name>
        <version>1</version>
        <fqname>IMySensor/default</fqname>
    </hal>
</manifest>
```

This file is included in the build via the `vintf_fragments:` field in `Android.bp`.

---

## Accessing the HAL from a Client (C++)

```cpp
#include <android/binder_manager.h>
#include <aidl/android/hardware/myhardware/IMySensor.h>

using aidl::android::hardware::myhardware::IMySensor;

std::shared_ptr<IMySensor> getHalService() {
    const std::string name = std::string(IMySensor::descriptor) + "/default";
    return IMySensor::fromBinder(
        ndk::SpAIBinder(AServiceManager_waitForService(name.c_str())));
}
```

Use `AServiceManager_checkService` for a non-blocking check, or `AServiceManager_waitForService` to block until the HAL is registered.

---

## Error Handling with `ScopedAStatus`

```cpp
// Return an error with a service-specific error code
return ndk::ScopedAStatus::fromServiceSpecificError(MY_ERROR_SENSOR_NOT_READY);

// Return a standard error
return ndk::ScopedAStatus::fromStatus(STATUS_BAD_VALUE);

// Check on the client side
ndk::ScopedAStatus status = hal->readTemperature(&temp);
if (!status.isOk()) {
    ALOGE("readTemperature failed: %s", status.getDescription().c_str());
}
```

---

## HIDL (Legacy — Android 8–10)

HIDL is deprecated. If you are maintaining an existing HIDL HAL:
- Interface files use `.hal` extension with `package android.hardware.*` syntax.
- Code generation uses `hidl-gen`.
- Transport is over HwBinder (`/dev/hwbinder`), not the regular binder.
- Registration uses `defaultPassthroughServiceImplementation<IFoo>()` (passthrough) or `registerAsService()` (binderized).

**Do not create new HIDL HALs.** Migrate existing ones to AIDL HAL.

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

The step-by-step AIDL HAL implementation is defined in the numbered Step sections below
(Step 1 through Step 5). Follow them in order: define the AIDL interface → implement
the C++ service → register it → add the VINTF manifest entry → run VTS.


## Troubleshooting

- **HAL service not found at boot** — verify the `init.rc` service entry and `VINTF` manifest entry match the registered service name exactly.
- **`PERMISSION_DENIED` from `AServiceManager_addService`** — SELinux policy is missing; add a `allow <domain> hal_<name>_hwservice:hwservice_manager add;` rule.
- **Client gets null from `AServiceManager_getService`** — the service process hasn't started yet; use `AServiceManager_waitForService()` with a timeout.
- **VTS test fails with `NOT_SUPPORTED`** — the method is declared in the AIDL interface but not fully implemented; return a proper status code.


## Pre-Commit Checklist

- [ ] Interface uses `@VintfStability` and `stability: "vintf"` in `.bp`.
- [ ] Service name follows `<descriptor>/default` or `<descriptor>/<instance>` pattern.
- [ ] `AServiceManager_addService` return code checked.
- [ ] `init.rc` file included via `init_rc:` in `Android.bp`.
- [ ] VINTF manifest fragment included via `vintf_fragments:` in `Android.bp`.
- [ ] `vendor: true` set in `Android.bp` for vendor partition binaries.
- [ ] Shared libraries listed with the NDK backend library: `android.hardware.foo-VN-ndk`.
- [ ] Thread pool configured with `ABinderProcess_setThreadPoolMaxThreadCount`.

---

## References

- [Implementing an AIDL HAL](https://source.android.com/docs/core/architecture/aidl/aidl-hals)
- [AIDL HAL Example in AOSP](https://source.android.com/docs/core/architecture/aidl/aidl-hals#aidl-hal-example)
- [VINTF Overview](https://source.android.com/docs/core/architecture/vintf)
- [Android Binder NDK](https://source.android.com/docs/core/architecture/aidl/aidl-backends#ndk)
