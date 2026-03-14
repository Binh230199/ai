---
name: cpp-ipc-mechanisms
description: >
  Use when designing, implementing, or reviewing inter-process communication (IPC)
  in C/C++ automotive embedded projects (IVI, HUD, RSE on Linux/QNX/Android).
  Covers D-Bus (libdbus / sdbus-c++), SOME/IP (vsomeip), Android Binder (AIDL/NDK),
  POSIX shared memory, UNIX domain sockets, message queues, and architectural
  considerations for choosing the right IPC mechanism.
argument-hint: <mechanism|interface> [design|implement|review]
---

# C/C++ IPC Mechanisms — Automotive Embedded

Expert practices for **inter-process communication** in automotive embedded systems:
**D-Bus** (Linux services), **SOME/IP** (AUTOSAR/SOA), **Android Binder** (AIDL),
and **POSIX IPC** primitives (shared memory, UNIX sockets, message queues).

---

## When to Use This Skill

- Designing the IPC boundary between two processes or services.
- Implementing a D-Bus service or client with `sdbus-c++` or raw `libdbus`.
- Setting up SOME/IP service-discovery and event subscription with `vsomeip`.
- Calling an Android HAL service via AIDL from native (NDK) code.
- Choosing between shared memory, sockets, or message queues for a data pipeline.
- Reviewing IPC code for security, performance, or correctness issues.

---

## IPC Mechanism Selection Guide

| Mechanism | Latency | Throughput | Discovery | Best For |
|---|---|---|---|---|
| **Android Binder** | Low | Medium | Static (AIDL IDL) | Android services, HAL |
| **D-Bus** | Medium | Low-medium | Dynamic (name bus) | Linux services, signals/events |
| **SOME/IP** | Medium | High | Dynamic (SD) | AUTOSAR SOA, ECU-to-ECU |
| **UNIX domain socket** | Very low | High | None (path-based) | Local high-throughput IPC |
| **POSIX shared memory** | Minimal | Very high | None (manual sync) | Large data, zero-copy |
| **POSIX message queue** | Low | Medium | None | Small messages, flow control |
| **QNX message passing** | Very low | High | None | QNX native RT IPC |

---

## D-Bus — sdbus-c++ (Recommended C++ API)

### Service (server side)

```cpp
// AdaptorDef: generated from D-Bus XML introspection or hand-written
#include <sdbus-c++/sdbus-c++.h>

class AudioService : public sdbus::AdaptorInterfaces<org::example::Audio_adaptor> {
public:
    explicit AudioService(sdbus::IConnection& connection)
        : AdaptorInterfaces(connection, sdbus::ObjectPath{"/org/example/Audio"})
    {
        registerAdaptor();
    }

    // Implements interface method
    int32_t SetVolume(int32_t level) override {
        level = std::clamp(level, 0, 100);
        current_volume_ = level;
        emitVolumeChanged(current_volume_);  // emit signal
        return current_volume_;
    }

private:
    int32_t current_volume_ = 50;
};

// main.cpp (service entry)
int main() {
    auto connection = sdbus::createSystemBusConnection("org.example.AudioService");
    AudioService svc(*connection);
    connection->enterEventLoop();
}
```

### Client (proxy side)

```cpp
#include <sdbus-c++/sdbus-c++.h>

class AudioClient : public sdbus::ProxyInterfaces<org::example::Audio_proxy> {
public:
    explicit AudioClient(sdbus::IConnection& connection)
        : ProxyInterfaces(
            connection,
            sdbus::ServiceName{"org.example.AudioService"},
            sdbus::ObjectPath{"/org/example/Audio"}
          )
    {
        registerProxy();
    }

    // Handle VolumeChanged signal
    void onVolumeChanged(int32_t newVolume) override {
        LOGD("Volume changed to: %d", newVolume);
    }
};

// Usage
auto conn = sdbus::createSystemBusConnection();
AudioClient client(*conn);
auto result = client.SetVolume(75);
conn->enterEventLoopAsync();
```

### Security: D-Bus Policy File

```xml
<!-- /etc/dbus-1/system.d/org.example.AudioService.conf -->
<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
    "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
    <policy user="audio_service">
        <allow own="org.example.AudioService"/>
    </policy>
    <policy context="default">
        <allow send_destination="org.example.AudioService"
               send_interface="org.example.Audio"
               send_member="SetVolume"/>
        <deny  send_destination="org.example.AudioService"/>
    </policy>
</busconfig>
```

---

## SOME/IP — vsomeip

### Service registration (server)

```cpp
#include <vsomeip/vsomeip.hpp>

constexpr vsomeip::service_t kService = 0x1234;
constexpr vsomeip::instance_t kInstance = 0x0001;
constexpr vsomeip::method_t   kMethodSetVolume = 0x0010;
constexpr vsomeip::event_t    kEventVolume = 0x8001;

class AudioVsomeipService {
public:
    AudioVsomeipService()
        : app_(vsomeip::runtime::get()->create_application("AudioService"))
    {}

    void init() {
        app_->init();
        app_->register_message_handler(
            kService, kInstance, kMethodSetVolume,
            [this](const std::shared_ptr<vsomeip::message>& msg) { handleSetVolume(msg); }
        );
        app_->offer_service(kService, kInstance);
        app_->offer_event(kService, kInstance, kEventVolume, {kEventVolume});
    }

    void run() { app_->start(); }

private:
    void handleSetVolume(const std::shared_ptr<vsomeip::message>& msg) {
        auto payload = msg->get_payload();
        uint8_t vol = payload->get_data()[0];
        volume_ = std::min(vol, uint8_t{100});

        // Send response
        auto resp = vsomeip::runtime::get()->create_response(msg);
        resp->set_payload(makePayload(&volume_, 1));
        app_->send(resp);

        // Fire event
        auto event_payload = makePayload(&volume_, 1);
        app_->notify(kService, kInstance, kEventVolume, event_payload);
    }

    std::shared_ptr<vsomeip::payload> makePayload(const uint8_t* data, std::size_t len) {
        auto p = vsomeip::runtime::get()->create_payload();
        p->set_data(data, len);
        return p;
    }

    std::shared_ptr<vsomeip::application> app_;
    uint8_t volume_ = 50;
};
```

---

## POSIX Shared Memory — Zero-Copy Data Pipeline

```cpp
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>

// Producer (writer process)
class SharedMemWriter {
public:
    explicit SharedMemWriter(const std::string& name, std::size_t size)
        : name_(name), size_(size)
    {
        fd_ = shm_open(name.c_str(), O_CREAT | O_RDWR, 0600);
        if (fd_ < 0) throw std::system_error(errno, std::system_category());
        if (ftruncate(fd_, static_cast<off_t>(size)) < 0)
            throw std::system_error(errno, std::system_category());
        ptr_ = mmap(nullptr, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd_, 0);
        if (ptr_ == MAP_FAILED) throw std::system_error(errno, std::system_category());
    }
    ~SharedMemWriter() {
        munmap(ptr_, size_);
        close(fd_);
        shm_unlink(name_.c_str());
    }

    void write(const void* data, std::size_t len) {
        assert(len <= size_);
        std::memcpy(ptr_, data, len);
        __sync_synchronize();  // memory barrier — or use std::atomic_thread_fence
    }

private:
    std::string name_;
    std::size_t size_;
    int         fd_;
    void*       ptr_ = MAP_FAILED;
};
```

**Warning**: Shared memory requires explicit synchronization (mutex in shared memory, or semaphore). Never use it across security boundaries without validation.

---

## UNIX Domain Sockets — High-Throughput Local IPC

```cpp
#include <sys/socket.h>
#include <sys/un.h>

// Server
class UnixSocketServer {
public:
    explicit UnixSocketServer(const std::string& path) : path_(path) {
        fd_ = socket(AF_UNIX, SOCK_STREAM, 0);
        if (fd_ < 0) throw std::system_error(errno, std::system_category());

        sockaddr_un addr{};
        addr.sun_family = AF_UNIX;
        std::strncpy(addr.sun_path, path.c_str(), sizeof(addr.sun_path) - 1);
        ::unlink(path.c_str());

        if (bind(fd_, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) < 0)
            throw std::system_error(errno, std::system_category());
        listen(fd_, 5);
    }

    int acceptClient() {
        int client = accept(fd_, nullptr, nullptr);
        if (client < 0) throw std::system_error(errno, std::system_category());
        return client;
    }

    ~UnixSocketServer() { close(fd_); ::unlink(path_.c_str()); }

private:
    std::string path_;
    int         fd_;
};
```

---

## Android Binder — AIDL from C++ (NDK)

```cpp
// Generated from IAudioService.aidl via aidl --lang=ndk
#include <aidl/org/example/IAudioService.h>
#include <android/binder_manager.h>
#include <android/binder_process.h>

// Client
void connectAndSetVolume(int32_t volume) {
    ABinderProcess_setThreadPoolMaxThreadCount(1);
    ABinderProcess_startThreadPool();

    const std::string serviceName = "org.example.IAudioService/default";
    ndk::SpAIBinder binder(AServiceManager_waitForService(serviceName.c_str()));
    if (!binder) {
        ALOGE("Cannot find service: %s", serviceName.c_str());
        return;
    }

    auto service = aidl::org::example::IAudioService::fromBinder(binder);
    int32_t result = 0;
    auto status = service->setVolume(volume, &result);
    if (!status.isOk()) {
        ALOGE("setVolume failed: %s", status.getDescription().c_str());
    }
}
```

---

## Architectural Guidelines

```
Rule 1: IPC is a boundary — domain logic must NEVER depend on transport details.
         Wrap every IPC call behind an interface/adapter.

Rule 2: Validate ALL data received over IPC before use.
         IPC data is untrusted input — apply input validation same as user input.

Rule 3: IPC calls can fail anytime — design for failure.
         Handle disconnection, timeout, and service unavailability gracefully.

Rule 4: Never share mutable state via shared memory without explicit synchronization.
         Use atomic operations or mutexes in shared memory for concurrent producers/consumers.

Rule 5: Keep IPC interfaces narrow and versioned.
         Adding a method is safe; removing or changing signatures requires negotiation.
```

---

## Clean Architecture Wrapper Pattern

```cpp
// Domain interface — no IPC dependency
class IAudioService {
public:
    virtual ~IAudioService() = default;
    virtual int setVolume(int level) = 0;
    virtual int getVolume() = 0;
};

// Adapter (lives at the infrastructure layer)
class DbusAudioServiceAdapter : public IAudioService {
public:
    explicit DbusAudioServiceAdapter(sdbus::IConnection& conn)
        : proxy_(conn) {}

    int setVolume(int level) override {
        return proxy_.SetVolume(static_cast<int32_t>(level));
    }
    int getVolume() override { return proxy_.GetVolume(); }

private:
    AudioClient proxy_;  // generated D-Bus proxy
};

// Use case / business logic only knows IAudioService*
class VolumeUseCase {
public:
    explicit VolumeUseCase(IAudioService& svc) : svc_(svc) {}
    void increaseVolume(int delta) { svc_.setVolume(svc_.getVolume() + delta); }
private:
    IAudioService& svc_;
};
```

---

## Security Considerations

- **D-Bus**: Always add a policy file restricting `own`/`send_destination` by user/group. Never rely on `context="default"` allowing all.
- **SOME/IP**: Use TLS transport (vsomeip-sec) for external-facing services on connected ECUs.
- **Shared memory**: Never use cross-UID shared memory without explicit access verification — map with minimum permissions (`PROT_READ` where possible).
- **Sockets**: For privileged operations over UNIX sockets, verify peer credentials with `SO_PEERCRED`.
- **Binder**: Android SELinux policy defines which processes can call which Binder interfaces.

---

## Prerequisites

- GCC 9+ or Clang 12+ toolchain installed.
- CMake 3.16+ on PATH.
- For cross-compilation: ARM/AArch64 sysroot or Android NDK r25+.
- `ninja` build tool recommended for faster builds.


## Step-by-Step Workflows

### Step 1: Select the IPC mechanism
Use the decision table (D-Bus, SOME/IP, Binder, POSIX shared memory, UNIX socket) for latency vs. complexity requirements.

### Step 2: Define the interface contract
Write the D-Bus XML, SOME/IP vsomeip JSON config, or AIDL file.

### Step 3: Implement the server / provider
Register the service; implement interface methods; use RAII for resource cleanup.

### Step 4: Implement the client / consumer
Connect to the service; add reconnection / retry logic for robustness.

### Step 5: Test in isolation
Write a loopback test (server + client in the same process) before testing cross-process.


## Troubleshooting

- **D-Bus connection refused** — verify the D-Bus service name is registered in a `.service` file; check that the bus daemon is running.
- **SOME/IP service not discovered** — check that both peers use the same multicast address and port in `vsomeip.json`; verify firewall rules.
- **Binder transaction fails with `DEAD_OBJECT`** — the remote process crashed; register a death listener with `linkToDeath()`.
- **POSIX shared memory access violation** — ensure both processes map the memory before accessing; use a mutex or semaphore for synchronization.


## Pre-Commit Checklist

- [ ] IPC mechanism choice justified in design comments (why D-Bus vs socket vs shared memory).
- [ ] Domain logic wrapped behind a pure interface — no direct IPC in business layer.
- [ ] All IPC data validated before use (length, range, null checks).
- [ ] Error handling present for disconnection and service unavailability.
- [ ] D-Bus policy file updated for new interfaces.
- [ ] Shared memory access protected by synchronization primitive.
- [ ] No blocking IPC calls on the main/UI thread.

---

## References

- [sdbus-c++ documentation](https://github.com/Kistler-Group/sdbus-cpp)
- [vsomeip User Guide](https://github.com/COVESA/vsomeip/wiki)
- [Android Binder NDK Guide](https://developer.android.com/ndk/guides/stable_aidl)
- [D-Bus Specification](https://dbus.freedesktop.org/doc/dbus-specification.html)
- [SOME/IP Specification (AUTOSAR)](https://www.autosar.org/fileadmin/standards/R22-11/FO/AUTOSAR_PRS_SOMEIPProtocol.pdf)
