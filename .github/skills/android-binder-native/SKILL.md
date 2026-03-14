---
name: android-binder-native
description: >
  Use when implementing or reviewing native C++ Binder services in AOSP using
  libbinder directly (BnInterface/BpInterface, Parcel, onTransact). Covers the
  IInterface pattern with DECLARE/IMPLEMENT_META_INTERFACE macros, server-side
  BnFoo stub, client-side BpFoo proxy, Parcel serialization, ServiceManager
  registration, ProcessState thread pool setup, and IBinder death notifications.
  Applies to AOSP system services, platform components, and vendor native services.
argument-hint: <service-name> [write|review|debug]
---

# Android Native Binder Service (libbinder C++)

Practices for writing correct native C++ Binder services in AOSP using
**libbinder** directly. This covers IVI, HUD, and RSE platform components on
**Android Automotive OS (AAOS)**.

Source of truth:
- [Android Binder IPC](https://source.android.com/docs/core/architecture/hidl/binder-ipc)
- AOSP source: `frameworks/native/libs/binder/`

---

## When to Use This Skill vs. AIDL

| Approach | When to Use |
|---|---|
| **Native libbinder** (this skill) | Maintaining existing AOSP system services; platform components that need direct Parcel control; learning how Binder works |
| **AIDL cpp backend** (see `android-aidl`) | New AOSP system services — generates BnFoo/BpFoo automatically |
| **AIDL NDK backend** (see `android-hal`) | Vendor HAL services, NDK-accessible services |

In modern AOSP development the AIDL compiler generates the `BnFoo`/`BpFoo` boilerplate from a `.aidl` file. Understanding the manual pattern is necessary for reading existing code and for cases where AIDL tooling is not used.

> **Note**: `libbinder` is a platform system library. It is **not** available to third-party apps via the NDK. Use this pattern only in AOSP platform code (system partition, vendor partition binaries built with Soong).

---

## Required Headers

```cpp
#include <binder/IInterface.h>      // IInterface, BnInterface, BpInterface
#include <binder/Parcel.h>          // Parcel
#include <binder/ProcessState.h>    // ProcessState
#include <binder/IPCThreadState.h>  // IPCThreadState
#include <binder/IServiceManager.h> // defaultServiceManager
#include <utils/RefBase.h>          // sp<T>, wp<T>
#include <utils/String16.h>         // String16
```

---

## Step 1 — Define the Interface (IFoo.h)

```cpp
// IFoo.h
#pragma once
#include <binder/IInterface.h>
#include <utils/String16.h>

namespace android {

class IFoo : public IInterface {
public:
    // DECLARE_META_INTERFACE generates:
    //   static sp<IFoo> asInterface(const sp<IBinder>& binder);
    //   virtual const String16& getInterfaceDescriptor() const;
    DECLARE_META_INTERFACE(Foo);

    // Transaction codes — each method maps to one code
    enum {
        GET_VALUE = IBinder::FIRST_CALL_TRANSACTION,
        SET_VALUE,
        GET_NAME,
    };

    // Pure virtual methods — the public API
    virtual int32_t getValue() = 0;
    virtual status_t setValue(int32_t value) = 0;
    virtual String16  getName() = 0;
};

// ---- Server-side stub (Binder Native) ----
class BnFoo : public BnInterface<IFoo> {
public:
    status_t onTransact(uint32_t code, const Parcel& data,
                        Parcel* reply, uint32_t flags = 0) override;
};

}  // namespace android
```

---

## Step 2 — Define the Proxy (BpFoo) and Implement the Interface (IFoo.cpp)

```cpp
// IFoo.cpp
#include "IFoo.h"
#include <binder/Parcel.h>

namespace android {

// IMPLEMENT_META_INTERFACE registers the interface descriptor string and
// provides the asInterface() factory that casts an IBinder to IFoo.
IMPLEMENT_META_INTERFACE(Foo, "com.example.IFoo");

// ---- Client-side proxy (Binder Proxy) ----
class BpFoo : public BpInterface<IFoo> {
public:
    explicit BpFoo(const sp<IBinder>& impl) : BpInterface<IFoo>(impl) {}

    int32_t getValue() override {
        Parcel data, reply;
        data.writeInterfaceToken(IFoo::getInterfaceDescriptor());
        remote()->transact(GET_VALUE, data, &reply);
        return reply.readInt32();
    }

    status_t setValue(int32_t value) override {
        Parcel data, reply;
        data.writeInterfaceToken(IFoo::getInterfaceDescriptor());
        data.writeInt32(value);
        status_t status = remote()->transact(SET_VALUE, data, &reply);
        return status;
    }

    String16 getName() override {
        Parcel data, reply;
        data.writeInterfaceToken(IFoo::getInterfaceDescriptor());
        remote()->transact(GET_NAME, data, &reply);
        String16 name;
        reply.readString16(&name);
        return name;
    }
};

// ---- Server-side onTransact dispatcher ----
status_t BnFoo::onTransact(uint32_t code, const Parcel& data,
                            Parcel* reply, uint32_t flags)
{
    // Verify the caller is talking to this interface
    CHECK_INTERFACE(IFoo, data, reply);

    switch (code) {
    case GET_VALUE:
        reply->writeInt32(getValue());
        return OK;

    case SET_VALUE: {
        int32_t value = data.readInt32();
        return setValue(value);
    }

    case GET_NAME:
        reply->writeString16(getName());
        return OK;

    default:
        return BBinder::onTransact(code, data, reply, flags);
    }
}

}  // namespace android
```

**Key rules:**
- `writeInterfaceToken` in the proxy and `CHECK_INTERFACE` in `onTransact` form a security check — they verify callers are not accidentally sending the wrong interface's Parcel.
- Always delegate unknown `code` values to `BBinder::onTransact()` (base class handles `INTERFACE_TRANSACTION` and `DUMP_TRANSACTION`).
- `onTransact` runs on a Binder thread pool thread — protect shared state with locks.

---

## Step 3 — Implement the Service

```cpp
// FooService.h
#pragma once
#include "IFoo.h"

namespace android {

class FooService : public BnFoo {
public:
    FooService() : value_(0) {}

    int32_t  getValue() override;
    status_t setValue(int32_t value) override;
    String16  getName() override;

private:
    mutable Mutex mutex_;
    int32_t value_;
};

}  // namespace android
```

```cpp
// FooService.cpp
#include "FooService.h"

namespace android {

int32_t FooService::getValue() {
    AutoMutex lock(mutex_);
    return value_;
}

status_t FooService::setValue(int32_t value) {
    AutoMutex lock(mutex_);
    value_ = value;
    return OK;
}

String16 FooService::getName() {
    return String16("FooService");
}

}  // namespace android
```

---

## Step 4 — Register the Service (Server main)

```cpp
// service_main.cpp
#include <binder/IPCThreadState.h>
#include <binder/IServiceManager.h>
#include <binder/ProcessState.h>
#include "FooService.h"

using namespace android;

int main(int /*argc*/, char* /*argv*/[]) {
    // Open /dev/binder and set up the thread pool
    sp<ProcessState> proc = ProcessState::self();
    proc->setThreadPoolMaxThreadCount(4);

    // Register the service with ServiceManager
    sp<IServiceManager> sm = defaultServiceManager();
    sm->addService(String16("com.example.foo"), new FooService());

    // Start the thread pool and block
    proc->startThreadPool();
    IPCThreadState::self()->joinThreadPool();

    return 0;  // unreachable
}
```

---

## Step 5 — Connect from a Client

```cpp
// client_example.cpp
#include <binder/IServiceManager.h>
#include <binder/IPCThreadState.h>
#include "IFoo.h"

using namespace android;

int main() {
    // Look up the service (blocks until available)
    sp<IBinder> binder = defaultServiceManager()->getService(String16("com.example.foo"));
    if (binder == nullptr) {
        ALOGE("Service not found");
        return 1;
    }

    // Cast to the typed interface proxy
    sp<IFoo> foo = interface_cast<IFoo>(binder);  // same as IFoo::asInterface(binder)

    foo->setValue(42);
    int32_t val = foo->getValue();
    ALOGI("getValue = %d", val);

    return 0;
}
```

For a non-blocking lookup:
```cpp
sp<IBinder> binder = defaultServiceManager()->checkService(String16("com.example.foo"));
// Returns nullptr immediately if not registered yet
```

---

## Parcel — Common Read/Write Methods

| Operation | Write (proxy) | Read (stub) |
|---|---|---|
| `bool` | `data.writeBool(b)` | `data.readBool(&b)` |
| `int32_t` | `data.writeInt32(n)` | `data.readInt32(&n)` or `data.readInt32()` |
| `int64_t` | `data.writeInt64(n)` | `data.readInt64(&n)` |
| `float` | `data.writeFloat(f)` | `data.readFloat(&f)` |
| `String16` | `data.writeString16(s)` | `data.readString16(&s)` |
| `sp<IBinder>` | `data.writeStrongBinder(b)` | `data.readStrongBinder()` |
| byte array | `data.write(buf, len)` | `data.read(buf, len)` |

**Order matters**: the proxy and the stub must read/write in the exact same order.

---

## Service Death Notification

```cpp
class FooDeathRecipient : public IBinder::DeathRecipient {
public:
    void binderDied(const wp<IBinder>& /*who*/) override {
        ALOGW("FooService died — reconnecting");
        // Re-acquire the service
    }
};

// Register on the client side
sp<FooDeathRecipient> deathRecipient = new FooDeathRecipient();
binder->linkToDeath(deathRecipient);

// Unregister (e.g., on clean shutdown)
binder->unlinkToDeath(deathRecipient);
```

---

## AOSP Build (Android.bp)

```soong
cc_binary {
    name: "com.example.foo-service",
    srcs: [
        "service_main.cpp",
        "FooService.cpp",
        "IFoo.cpp",
    ],
    shared_libs: [
        "libbinder",
        "libutils",
        "liblog",
    ],
    // For a system service (system partition):
    // system_ext_specific: true,
    // For a vendor service:
    // vendor: true,
}

cc_binary {
    name: "com.example.foo-client",
    srcs: ["client_example.cpp", "IFoo.cpp"],
    shared_libs: ["libbinder", "libutils", "liblog"],
}
```

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

The step-by-step implementation workflow is defined in the numbered Step sections below
(Step 1 through Step 5). Follow them in order: define the IFoo interface → implement
BpFoo proxy → implement BnFoo stub → register with ServiceManager → use from client.


## Troubleshooting

- **`ServiceManager::getService()` returns null** — the server hasn't registered yet; retry with backoff or use `waitForService()`.
- **Parcel `BAD_TYPE` crash** — read arguments from Parcel in exactly the same order they were written.
- **`FAILED BINDER TRANSACTION`** — transaction data exceeds the 1 MB Binder buffer limit; chunk large data or use file descriptors.
- **`DeadObjectException` / `DEAD_OBJECT` status** — service process crashed; use `linkToDeath()` to register a death handler.


## Pre-Commit Checklist

- [ ] `IMPLEMENT_META_INTERFACE` descriptor string matches across proxy and stub.
- [ ] `CHECK_INTERFACE` called at the start of every `onTransact`.
- [ ] Unknown transaction codes delegate to `BBinder::onTransact`.
- [ ] Proxy writes and stub reads Parcel fields in identical order.
- [ ] `onTransact` does not hold a non-recursive mutex across slow operations (risk of deadlock on re-entrant calls).
- [ ] Shared state in the service protected by a mutex (`Mutex` / `AutoMutex` from `<utils/Mutex.h>`).
- [ ] Thread pool size set via `setThreadPoolMaxThreadCount` before `startThreadPool`.
- [ ] Death recipient registered if the client needs to react to service crash.
- [ ] `libbinder`, `libutils`, `liblog` listed in `shared_libs` in `Android.bp`.

---

## References

- [Binder IPC — source.android.com](https://source.android.com/docs/core/architecture/hidl/binder-ipc)
- [BinderDemo (gburca) — annotated example](https://github.com/gburca/BinderDemo)
- AOSP source: `frameworks/native/libs/binder/`
- AOSP example: `frameworks/native/services/` (surfaceflinger, inputflinger)
