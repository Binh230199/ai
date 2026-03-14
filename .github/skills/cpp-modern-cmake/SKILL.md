---
name: cpp-modern-cmake
description: >
  Use when writing, reviewing, or debugging CMake build scripts for C/C++ projects
  in embedded automotive context (IVI, HUD, RSE on Linux/QNX/Android NDK).
  Covers modern target-based CMake (3.16+), CMakePresets, toolchain files,
  cross-compilation setup, install rules, packaging, and CI/CD integration.
argument-hint: <CMakeLists|toolchain|preset> [write|review|fix]
---

# Modern CMake — C/C++ Embedded Projects

Expert practices for writing **modern, target-based CMake** (version 3.16+) for
**Android NDK**, **Linux BSP**, and **QNX** embedded automotive targets.

Standards baseline: **CMake 3.16+** (prefer 3.25+ for presets v4) · **No legacy patterns**.

---

## When to Use This Skill

- Writing or reviewing `CMakeLists.txt` for any C/C++ module.
- Setting up toolchain files for ARM/QNX/Android NDK cross-compilation.
- Configuring `CMakePresets.json` for local dev and CI.
- Adding unit test targets (`ctest`) to a project.
- Creating install rules and packaging (`CPack`).
- Adding `clang-tidy`, `cppcheck`, or `sanitizer` flags to a build.

---

## The One Rule: Think in Targets

Every modern CMake project revolves around **targets** with properly scoped properties.

```
PRIVATE   — used only by this target (implementation detail)
INTERFACE — propagated to consumers, NOT used by this target (header-only libs)
PUBLIC    — used by this target AND propagated to consumers
```

Violating this scope rule causes transitive dependency pollution.

---

## Project Skeleton

```cmake
cmake_minimum_required(VERSION 3.16)
project(MyCarPlugin VERSION 1.2.0 LANGUAGES CXX C)

# Guard against in-source builds
if(PROJECT_SOURCE_DIR STREQUAL PROJECT_BINARY_DIR)
    message(FATAL_ERROR "In-source builds not allowed. Use: cmake -B build")
endif()

# Global C++ standard (min — targets can override upward)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)   # -std=c++17, NOT -std=gnu++17

# Export compile commands for clang-tidy / IDEs
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Project-wide options
option(BUILD_TESTS    "Build unit tests"     OFF)
option(ENABLE_ASAN    "Enable AddressSanitizer" OFF)
option(ENABLE_TIDY    "Run clang-tidy"       OFF)

add_subdirectory(src)
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

---

## Library Target — Best Practices

```cmake
# src/CMakeLists.txt
add_library(car_plugin SHARED)   # or STATIC, MODULE

# Sources — always list explicitly, no GLOB
target_sources(car_plugin
    PRIVATE
        src/CarPlugin.cpp
        src/AudioManager.cpp
    PUBLIC
        FILE_SET HEADERS
        BASE_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/include
        FILES
            include/car_plugin/CarPlugin.h
            include/car_plugin/AudioManager.h
)

# Include directories — target-scoped, never global
target_include_directories(car_plugin
    PUBLIC  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
            $<INSTALL_INTERFACE:include>   # for installed headers
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Compile options — scoped, warning-safe
target_compile_options(car_plugin
    PRIVATE
        -Wall -Wextra -Wpedantic -Wshadow -Wno-unused-parameter
        $<$<CXX_COMPILER_ID:Clang>:-Weverything -Wno-c++98-compat>
)

# Compile definitions — no -D in CFLAGS manually
target_compile_definitions(car_plugin
    PRIVATE
        CAR_PLUGIN_VERSION_MAJOR=${PROJECT_VERSION_MAJOR}
    PUBLIC
        $<$<BOOL:${ENABLE_FEATURE_X}>:FEATURE_X_ENABLED>
)

# Dependencies — link against OTHER targets, not raw -l flags
find_package(dbus-1 REQUIRED)
target_link_libraries(car_plugin
    PUBLIC  dbus-1::dbus-1
    PRIVATE Threads::Threads
)
```

---

## Executable Target

```cmake
add_executable(car_daemon)
target_sources(car_daemon PRIVATE main.cpp)
target_link_libraries(car_daemon PRIVATE car_plugin)

# RPATH for installed binary (finds shared libs relative to executable)
set_target_properties(car_daemon PROPERTIES
    INSTALL_RPATH "$ORIGIN/../lib"
    BUILD_WITH_INSTALL_RPATH OFF
)
```

---

## CMakePresets.json

```json
{
    "version": 4,
    "configurePresets": [
        {
            "name": "base",
            "hidden": true,
            "generator": "Ninja",
            "binaryDir": "${sourceDir}/build/${presetName}",
            "cacheVariables": {
                "CMAKE_EXPORT_COMPILE_COMMANDS": "ON"
            }
        },
        {
            "name": "host-debug",
            "displayName": "Host — Debug",
            "inherits": "base",
            "cacheVariables": {
                "CMAKE_BUILD_TYPE": "Debug",
                "BUILD_TESTS": "ON",
                "ENABLE_ASAN": "ON"
            }
        },
        {
            "name": "cross-arm-release",
            "displayName": "ARM Cortex-A — Release",
            "inherits": "base",
            "toolchainFile": "${sourceDir}/cmake/toolchains/aarch64-linux-gnu.cmake",
            "cacheVariables": {
                "CMAKE_BUILD_TYPE": "Release",
                "BUILD_TESTS": "OFF"
            }
        }
    ],
    "buildPresets": [
        { "name": "host-debug",       "configurePreset": "host-debug" },
        { "name": "cross-arm-release","configurePreset": "cross-arm-release" }
    ],
    "testPresets": [
        {
            "name": "unit",
            "configurePreset": "host-debug",
            "output": { "outputOnFailure": true },
            "execution": { "jobs": 4 }
        }
    ]
}
```

---

## Toolchain File — ARM Cross-Compilation

```cmake
# cmake/toolchains/aarch64-linux-gnu.cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(CROSS_COMPILE aarch64-linux-gnu-)
set(CMAKE_C_COMPILER   ${CROSS_COMPILE}gcc)
set(CMAKE_CXX_COMPILER ${CROSS_COMPILE}g++)
set(CMAKE_STRIP        ${CROSS_COMPILE}strip)
set(CMAKE_AR           ${CROSS_COMPILE}ar)

# Sysroot (where target headers/libs live on build machine)
set(CMAKE_SYSROOT "/opt/sysroot-aarch64")
set(CMAKE_FIND_ROOT_PATH "${CMAKE_SYSROOT}")

# Only search target sysroot for libraries and headers
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
```

---

## Finding Dependencies

```cmake
# Correct: use find_package with imported targets
find_package(OpenSSL REQUIRED)
target_link_libraries(my_target PRIVATE OpenSSL::SSL OpenSSL::Crypto)

find_package(Threads REQUIRED)
target_link_libraries(my_target PRIVATE Threads::Threads)

# pkg-config fallback for libraries without CMake support
find_package(PkgConfig REQUIRED)
pkg_check_modules(DBUS REQUIRED IMPORTED_TARGET dbus-1)
target_link_libraries(my_target PRIVATE PkgConfig::DBUS)

# Never do this:
# target_link_libraries(my_target -lpthread)               # WRONG
# include_directories(/usr/include/dbus-1.0)               # WRONG
```

---

## sanitizers

```cmake
# cmake/Sanitizers.cmake
function(enable_sanitizers target)
    if(ENABLE_ASAN)
        target_compile_options(${target} PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(${target}    PRIVATE -fsanitize=address,undefined)
    endif()
    if(ENABLE_TSAN)
        target_compile_options(${target} PRIVATE -fsanitize=thread)
        target_link_options(${target}    PRIVATE -fsanitize=thread)
    endif()
endfunction()
```

---

## clang-tidy Integration

```cmake
if(ENABLE_TIDY)
    find_program(CLANG_TIDY_EXE NAMES clang-tidy-16 clang-tidy REQUIRED)
    set(CLANG_TIDY_CMD "${CLANG_TIDY_EXE}" "--config-file=${CMAKE_SOURCE_DIR}/.clang-tidy")
    set_target_properties(my_target PROPERTIES CXX_CLANG_TIDY "${CLANG_TIDY_CMD}")
endif()
```

---

## Install Rules

```cmake
include(GNUInstallDirs)

install(TARGETS car_plugin car_daemon
    RUNTIME  DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY  DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE  DESTINATION ${CMAKE_INSTALL_LIBDIR}
    FILE_SET HEADERS DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

# CMake package config for downstream find_package
install(EXPORT CarPluginTargets
    FILE        CarPluginTargets.cmake
    NAMESPACE   CarPlugin::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/CarPlugin
)
```

---

## Anti-Patterns — Never Do This

```cmake
# WRONG: glob for sources (CMake won't re-run when you add files)
file(GLOB_RECURSE SRCS src/*.cpp)

# WRONG: global include dirs leak into everything
include_directories(${SOME_LIB_INCLUDE_DIRS})

# WRONG: raw link flags instead of imported targets
target_link_libraries(foo -lssl -lcrypto)

# WRONG: modifying CMAKE_CXX_FLAGS directly (affects all targets)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")

# WRONG: in-source build not prevented
# (add the guard shown in the skeleton above)
```

---

## Prerequisites

- GCC 9+ or Clang 12+ toolchain installed.
- CMake 3.16+ on PATH.
- For cross-compilation: ARM/AArch64 sysroot or Android NDK r25+.
- `ninja` build tool recommended for faster builds.


## Step-by-Step Workflows

### Step 1: Create a target-based CMakeLists.txt
Use `add_library` / `add_executable`; never use global `include_directories` or `add_definitions`.

### Step 2: Set compile features (not flags)
Use `target_compile_features(mylib PUBLIC cxx_std_17)` instead of `-std=c++17` raw flag.

### Step 3: Add CMakePresets.json
Define `configure`, `build`, and `test` presets; commit the presets file to version control.

### Step 4: Add install rules
Use `install(TARGETS ...)` with `EXPORT` for downstream consumers; set correct `DESTINATION` paths.

### Step 5: Validate
Run `cmake --preset default && cmake --build --preset default && ctest --preset default`.


## Troubleshooting

- **`target_link_libraries` dependency not propagated** — use `PUBLIC` for APIs used in headers; `PRIVATE` for implementation-only; `INTERFACE` for header-only libs.
- **`find_package` finds the wrong version** — set `CMAKE_PREFIX_PATH` explicitly; use `find_package(<pkg> <version> EXACT REQUIRED)`.
- **`cmake --install` installs to system paths** — always pass `--prefix` or set `CMAKE_INSTALL_PREFIX` in the preset to avoid polluting `/usr/local`.
- **Build is slow** — enable `CMAKE_EXPORT_COMPILE_COMMANDS=ON`; use `Ninja` generator; enable ccache with `CMAKE_CXX_COMPILER_LAUNCHER=ccache`.


## Pre-Commit Checklist

- [ ] `cmake_minimum_required(VERSION 3.16)` (or higher) at top.
- [ ] No `include_directories()` — use `target_include_directories()`.
- [ ] No `link_libraries()` — use `target_link_libraries()`.
- [ ] No raw `-l` flags — use imported targets or `PkgConfig::*`.
- [ ] No `file(GLOB ...)` for sources — list files explicitly.
- [ ] All targets have correct `PUBLIC`/`PRIVATE`/`INTERFACE` scopes.
- [ ] `CMAKE_CXX_EXTENSIONS OFF` to enforce `-std=c++17` not `-std=gnu++17`.
- [ ] `CMakePresets.json` exists with at least `host-debug` and a cross preset.
- [ ] `CMAKE_EXPORT_COMPILE_COMMANDS ON` for tooling.

---

## References

- [Modern CMake Book](https://cliutils.gitlab.io/modern-cmake/)
- [CMake Documentation](https://cmake.org/documentation/)
- [CMake Presets Reference](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html)
- [Professional CMake (Craig Scott)](https://crascit.com/professional-cmake/)
