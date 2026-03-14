---
name: cpp-cross-compilation
description: >
  Use when setting up, debugging, or reviewing cross-compilation toolchains for
  C/C++ embedded projects targeting ARM (Linux), AArch64 (Android NDK), or QNX.
  Covers toolchain selection, sysroot configuration, CMake toolchain files,
  pkg-config wrappers, multilib, Android NDK integration, and common pitfalls.
argument-hint: <target-arch|platform> [setup|debug|review]
---

# C/C++ Cross-Compilation — Embedded Targets

Expert practices for cross-compiling C/C++ code from an **x86-64 Linux or Windows
(WSL)** host to embedded automotive targets: **ARM/AArch64 Linux**, **QNX SDP**,
and **Android NDK** (armeabi-v7a, arm64-v8a, x86_64).

---

## When to Use This Skill

- Setting up a cross-compilation toolchain for the first time.
- Writing or auditing a CMake toolchain file.
- Debugging "host binary runs, target binary segfaults" class problems.
- Integrating Android NDK into a CMake or Makefile project.
- Configuring `pkg-config` to find target libraries, not host libraries.
- Wrapping cross-toolchain in a CI/CD pipeline.

---

## Toolchain Selection

| Target | Toolchain | Location |
|---|---|---|
| AArch64 Linux (generic) | `aarch64-linux-gnu-gcc` | `apt install gcc-aarch64-linux-gnu` |
| ARMv7 Linux (hard-float) | `arm-linux-gnueabihf-gcc` | `apt install gcc-arm-linux-gnueabihf` |
| QNX SDP 7.1 (AArch64) | `aarch64-unknown-nto-qnx7.1.0-g++` | QNX SDP installer |
| Android NDK (AArch64) | `clang` from NDK toolchain | Android NDK r25c+ |
| Android NDK (ARM32) | `clang` from NDK toolchain | Android NDK, `-DANDROID_ABI=armeabi-v7a` |

---

## CMake Toolchain File — AArch64 Linux

```cmake
# cmake/toolchains/aarch64-linux-gnu.cmake
set(CMAKE_SYSTEM_NAME    Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

# Toolchain prefix
set(CROSS  "aarch64-linux-gnu-")
set(CMAKE_C_COMPILER   "${CROSS}gcc")
set(CMAKE_CXX_COMPILER "${CROSS}g++")
set(CMAKE_AR           "${CROSS}ar"    CACHE FILEPATH "Archiver")
set(CMAKE_RANLIB       "${CROSS}ranlib" CACHE FILEPATH "Ranlib")
set(CMAKE_STRIP        "${CROSS}strip" CACHE FILEPATH "Strip")
set(CMAKE_OBJCOPY      "${CROSS}objcopy" CACHE FILEPATH "Objcopy")

# Sysroot
set(CMAKE_SYSROOT "/opt/sysroot-aarch64-linux-gnu")

# Root path priority — never search host paths for target libraries
set(CMAKE_FIND_ROOT_PATH "${CMAKE_SYSROOT}")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)   # build tools from HOST
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)    # libs from TARGET sysroot
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)    # headers from TARGET sysroot
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
```

```bash
# Usage
cmake -B build/aarch64 \
      --toolchain cmake/toolchains/aarch64-linux-gnu.cmake \
      -DCMAKE_BUILD_TYPE=Release
cmake --build build/aarch64 -j$(nproc)
```

---

## CMake Toolchain File — QNX SDP 7.1

```cmake
# cmake/toolchains/qnx-aarch64.cmake
set(CMAKE_SYSTEM_NAME  QNX)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

# QNX SDP must be sourced before cmake runs:
# source /opt/qnx710/qnxsdp-env.sh

set(QNX_HOST   "$ENV{QNX_HOST}")
set(QNX_TARGET "$ENV{QNX_TARGET}")

set(CMAKE_C_COMPILER   "${QNX_HOST}/usr/bin/aarch64-unknown-nto-qnx7.1.0-gcc")
set(CMAKE_CXX_COMPILER "${QNX_HOST}/usr/bin/aarch64-unknown-nto-qnx7.1.0-g++")
set(CMAKE_AR           "${QNX_HOST}/usr/bin/aarch64-unknown-nto-qnx7.1.0-ar")

set(CMAKE_SYSROOT "${QNX_TARGET}")
set(CMAKE_FIND_ROOT_PATH "${QNX_TARGET}")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)

# QNX-specific flags
add_compile_options(-D_QNX_SOURCE -Vgcc_ntoaarch64le)
```

---

## Android NDK Integration

### Via CMake toolchain (standalone)

```cmake
# Provided by the NDK itself at: <ndk>/build/cmake/android.toolchain.cmake
cmake -B build/android-arm64 \
    -DCMAKE_TOOLCHAIN_FILE="${ANDROID_NDK}/build/cmake/android.toolchain.cmake" \
    -DANDROID_ABI=arm64-v8a \
    -DANDROID_PLATFORM=android-29 \
    -DANDROID_STL=c++_shared \
    -DANDROID_ARM_NEON=ON \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo
```

### Via AOSP Soong (Android.bp)

```
cc_library_shared {
    name: "libcar_plugin",
    cppflags: ["-std=c++17", "-Wall", "-Wextra"],
    srcs: ["src/CarPlugin.cpp"],
    shared_libs: ["libbinder", "libutils"],
    export_include_dirs: ["include"],
}
```

---

## pkg-config for Cross-Compilation

The classic mistake: host `pkg-config` returns host library paths.

```bash
# WRONG — returns host paths
pkg-config --libs dbus-1

# CORRECT — configure for target sysroot
export PKG_CONFIG_SYSROOT_DIR=/opt/sysroot-aarch64-linux-gnu
export PKG_CONFIG_LIBDIR=${PKG_CONFIG_SYSROOT_DIR}/usr/lib/pkgconfig:${PKG_CONFIG_SYSROOT_DIR}/usr/share/pkgconfig
export PKG_CONFIG_PATH=""   # disable host search
pkg-config --libs dbus-1    # now returns target paths
```

In CMake, use a wrapper script or set `PKG_CONFIG_EXECUTABLE` to a cross-aware script:

```cmake
# cmake/toolchains/aarch64-linux-gnu.cmake (add to toolchain)
set(PKG_CONFIG_EXECUTABLE "${CMAKE_CURRENT_LIST_DIR}/../scripts/pkg-config-aarch64.sh")
```

```bash
#!/bin/bash
# scripts/pkg-config-aarch64.sh
export PKG_CONFIG_SYSROOT_DIR=/opt/sysroot-aarch64-linux-gnu
export PKG_CONFIG_LIBDIR=${PKG_CONFIG_SYSROOT_DIR}/usr/lib/pkgconfig
export PKG_CONFIG_PATH=""
exec pkg-config "$@"
```

---

## Sysroot Construction

A **sysroot** is a directory tree that mirrors the target filesystem, containing headers and libraries needed for compilation and linking.

### Option A: Extract from target rootfs

```bash
# From a built Yocto image
bitbake -c populate_sdk myimage
# Installs SDK to /opt/poky/<version>/sysroots/aarch64-poky-linux/

# Or manually sync from target
rsync -avz \
    --include='*.h' --include='*.so*' --include='*.a' \
    --include='*/' --exclude='*' \
    root@192.168.1.100:/usr/    /opt/sysroot-aarch64/usr/
```

### Option B: Debian multiarch

```bash
dpkg --add-architecture arm64
apt update
apt install libdbus-1-dev:arm64 libssl-dev:arm64
# Libraries installed to /usr/lib/aarch64-linux-gnu/
# CMake sysroot = /  but use CMAKE_LIBRARY_ARCHITECTURE = aarch64-linux-gnu
```

---

## Common Cross-Compilation Pitfalls

| Problem | Root Cause | Fix |
|---|---|---|
| `Exec format error` | Built for wrong arch | Verify with `file ./binary` and `readelf -h` |
| `GLIBC_2.33 not found` on target | Host toolchain too new | Use older toolchain or match sysroot GLIBC version |
| `cannot find -lssl` | pkg-config returns host paths | Fix `PKG_CONFIG_LIBDIR` as shown above |
| CMake uses host compiler for first run | Toolchain file not passed | Always use `--toolchain` or `-DCMAKE_TOOLCHAIN_FILE=` |
| `pthread` not linked | Missing `Threads::Threads` | `find_package(Threads REQUIRED)` + link |
| RPATH wrong in installed binary | Default RPATH cleared on install | Set `INSTALL_RPATH "$ORIGIN/../lib"` |

---

## Detecting Cross vs. Native Build at CMake Time

```cmake
if(CMAKE_CROSSCOMPILING)
    message(STATUS "Cross-compiling for ${CMAKE_SYSTEM_PROCESSOR}")
    # Disable tests that can't run on build machine
    set(BUILD_TESTS OFF CACHE BOOL "" FORCE)
else()
    message(STATUS "Native build for ${CMAKE_HOST_SYSTEM_PROCESSOR}")
endif()
```

---

## CI/CD Pipeline Integration

```bash
#!/usr/bin/env bash
set -euo pipefail

# Source QNX environment if building for QNX
if [[ "${TARGET_PLATFORM:-}" == "qnx" ]]; then
    # shellcheck source=/dev/null
    source /opt/qnx710/qnxsdp-env.sh
fi

cmake -B build \
    --toolchain "cmake/toolchains/${TARGET_PLATFORM:-aarch64-linux-gnu}.cmake" \
    -DCMAKE_BUILD_TYPE="${BUILD_TYPE:-Release}" \
    -DBUILD_TESTS=OFF

cmake --build build -j"${NPROC:-$(nproc)}"
cmake --install build --prefix "artifacts/${TARGET_PLATFORM}"
```

---

## Quick Verification Commands

```bash
# 1. Confirm binary architecture
file ./build/car_daemon
# → ELF 64-bit LSB executable, ARM aarch64

# 2. Confirm GLIBC version requirements
objdump -T ./build/car_daemon | grep GLIBC | sed 's/.*GLIBC_//' | sort -V | tail -1

# 3. List shared library dependencies
aarch64-linux-gnu-readelf -d ./build/libcar_plugin.so | grep NEEDED

# 4. Check RPATH
chrpath -l ./build/car_daemon   # or: patchelf --print-rpath
```

---

## Prerequisites

- GCC 9+ or Clang 12+ toolchain installed.
- CMake 3.16+ on PATH.
- For cross-compilation: ARM/AArch64 sysroot or Android NDK r25+.
- `ninja` build tool recommended for faster builds.


## Step-by-Step Workflows

### Step 1: Select the toolchain
Choose a prebuilt toolchain (ARM, AArch64, QNX) or the Android NDK for Android targets.

### Step 2: Write the CMake toolchain file
Set `CMAKE_SYSTEM_NAME`, `CMAKE_C_COMPILER`, `CMAKE_CXX_COMPILER`, and `CMAKE_SYSROOT`.

### Step 3: Configure with CMakePresets
Add a `crossCompile` preset referencing the toolchain file; set `CMAKE_BUILD_TYPE`.

### Step 4: Build and verify the binary
Run `cmake --preset crossCompile && cmake --build ...`; verify target arch with `file output.elf` or `readelf -h`.

### Step 5: Deploy and test on target
Copy via `scp` or `adb push`; run on target; check for missing shared library errors (`ldd` equivalent).


## Troubleshooting

- **`wrong ELF class` runtime error** — a host binary is being linked instead of the target; verify `CROSS_COMPILE` prefix and sysroot configuration.
- **`cmake` picks the wrong compiler** — explicitly set `CMAKE_C_COMPILER` and `CMAKE_CXX_COMPILER` in the toolchain file; do not rely on `PATH`.
- **`pkg-config` returns host paths** — use a target-specific `pkg-config` wrapper that sets `PKG_CONFIG_SYSROOT_DIR`; see the dedicated section below.
- **Shared library not found on target** — check `RPATH` with `readelf -d output.elf`; set `CMAKE_INSTALL_RPATH` to the target library path.


## Pre-Commit Checklist

- [ ] Toolchain file specifies `CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY`.
- [ ] `pkg-config` wrapper script used so host pkg-config is not polluting.
- [ ] Binary verified with `file` command to match target architecture.
- [ ] GLIBC version requirement checked against target system version.
- [ ] RPATH set correctly for installed binary (`$ORIGIN/../lib`).
- [ ] CI pipeline passes `--toolchain` flag explicitly, not via `CMAKE_TOOLCHAIN_FILE` in cache.

---

## References

- [CMake Cross Compiling Guide](https://cmake.org/cmake/help/latest/manual/cmake-toolchains.7.html)
- [Android NDK CMake Guide](https://developer.android.com/ndk/guides/cmake)
- [QNX SDP 7.1 Build Environment](https://www.qnx.com/developers/docs/7.1/)
- [Crosstool-NG](https://crosstool-ng.github.io/)
