---
name: cpp-unit-testing
description: >
  Use when writing, reviewing, or debugging C++ unit tests with Google Test (gtest)
  and Google Mock (gmock) in automotive embedded projects (IVI, HUD, RSE on Linux/QNX/Android NDK).
  Covers test structure, AAA pattern, fixture design, mock creation, parameterized tests,
  death tests, test doubles, CMake integration, and code coverage.
argument-hint: <class-or-module> [write|review|coverage]
---

# C++ Unit Testing — Google Test & Google Mock

Expert practices for writing fast, deterministic, well-structured unit tests using
**gtest** (GoogleTest) and **gmock** (GoogleMock) for automotive embedded C++ code.

Standards baseline: **googletest 1.12+** · **C++17** · **CMake FetchContent or find_package**.

---

## When to Use This Skill

- Writing new unit tests for a C++ class or free function.
- Reviewing existing tests for quality, completeness, and isolation.
- Mocking hardware abstraction layers (HAL) or OS interfaces.
- Setting up gtest + gmock in a new CMake project.
- Adding code coverage (`lcov` / `gcovr`) to CI.
- Writing characterization tests as a safety net before refactoring legacy code.

---

## CMake Setup

### Option A: FetchContent (recommended for new projects)

```cmake
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG        v1.14.0
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)  # Windows only
set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)
```

### Option B: find_package (system-installed or vendored)

```cmake
find_package(GTest REQUIRED)
```

### Test target wiring

```cmake
# tests/CMakeLists.txt
add_executable(audio_manager_test AudioManagerTest.cpp)
target_link_libraries(audio_manager_test
    PRIVATE
        car_plugin           # unit under test
        GTest::gtest_main    # includes main()
        GTest::gmock
)

include(GoogleTest)
gtest_discover_tests(audio_manager_test)  # auto-registers with ctest
```

---

## Test Structure — AAA Pattern

```cpp
// tests/AudioManagerTest.cpp
#include <gtest/gtest.h>
#include "AudioManager.h"

// ── Fixture ──────────────────────────────────────────────────────
class AudioManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        manager_ = std::make_unique<AudioManager>(kDefaultSampleRate);
    }

    void TearDown() override {
        // unique_ptr cleans up automatically; explicit if needed
    }

    static constexpr int kDefaultSampleRate = 48000;
    std::unique_ptr<AudioManager> manager_;
};

// ── Tests ─────────────────────────────────────────────────────────
// Naming: MethodName_StateUnderTest_ExpectedBehavior

TEST_F(AudioManagerTest, SetVolume_ValidRange_StoresValue) {
    // Arrange
    constexpr int kVolume = 75;

    // Act
    manager_->setVolume(kVolume);

    // Assert
    EXPECT_EQ(manager_->getVolume(), kVolume);
}

TEST_F(AudioManagerTest, SetVolume_AboveMax_ClampsToMax) {
    // Arrange
    constexpr int kAboveMax = 200;

    // Act
    manager_->setVolume(kAboveMax);

    // Assert
    EXPECT_EQ(manager_->getVolume(), AudioManager::kMaxVolume);
}

TEST_F(AudioManagerTest, SetVolume_BelowMin_ClampsToZero) {
    manager_->setVolume(-10);
    EXPECT_EQ(manager_->getVolume(), 0);
}
```

---

## Google Mock — Mocking Dependencies

```cpp
// include/IHalAudio.h — dependency interface
class IHalAudio {
public:
    virtual ~IHalAudio() = default;
    virtual int  openStream(int sampleRate) = 0;
    virtual void closeStream(int handle)    = 0;
    virtual void write(int handle, const std::vector<int16_t>& samples) = 0;
};
```

```cpp
// tests/mocks/MockHalAudio.h
#include <gmock/gmock.h>
#include "IHalAudio.h"

class MockHalAudio : public IHalAudio {
public:
    MOCK_METHOD(int,  openStream,  (int sampleRate),                         (override));
    MOCK_METHOD(void, closeStream, (int handle),                              (override));
    MOCK_METHOD(void, write,       (int handle, const std::vector<int16_t>&), (override));
};
```

```cpp
// tests/AudioPlayerTest.cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "AudioPlayer.h"
#include "mocks/MockHalAudio.h"

using ::testing::Return;
using ::testing::StrictMock;
using ::testing::InSequence;
using ::testing::_;

class AudioPlayerTest : public ::testing::Test {
protected:
    StrictMock<MockHalAudio> hal_;  // StrictMock: fails on unexpected calls
    // NiceMock<MockHalAudio> hal_; // NiceMock: ignores unexpected calls
};

TEST_F(AudioPlayerTest, Play_ValidFile_OpensStreamAndWrites) {
    // Arrange
    constexpr int kHandle = 42;
    EXPECT_CALL(hal_, openStream(48000)).WillOnce(Return(kHandle));
    EXPECT_CALL(hal_, write(kHandle, _)).Times(::testing::AtLeast(1));
    EXPECT_CALL(hal_, closeStream(kHandle)).Times(1);

    AudioPlayer player(&hal_);

    // Act
    player.play("sine_440hz.wav");

    // Assert — expectations verified automatically by StrictMock on destruction
}

TEST_F(AudioPlayerTest, Play_HalOpenFails_ReturnsError) {
    EXPECT_CALL(hal_, openStream(_)).WillOnce(Return(-1));
    AudioPlayer player(&hal_);

    EXPECT_EQ(player.play("test.wav"), AudioPlayer::Error::kHalOpenFailed);
}
```

---

## Matchers Reference

```cpp
// Equality
EXPECT_EQ(actual, expected);
EXPECT_NE(actual, expected);
EXPECT_LT(a, b);   EXPECT_LE(a, b);
EXPECT_GT(a, b);   EXPECT_GE(a, b);

// Floating point
EXPECT_FLOAT_EQ(3.14f, result);
EXPECT_NEAR(expected, actual, 0.001);

// Strings
EXPECT_STREQ("hello", cstr);
EXPECT_THAT(str, ::testing::HasSubstr("audio"));
EXPECT_THAT(str, ::testing::StartsWith("Car"));

// Collections
EXPECT_THAT(vec, ::testing::ElementsAre(1, 2, 3));
EXPECT_THAT(vec, ::testing::Contains(42));
EXPECT_THAT(vec, ::testing::SizeIs(3));
EXPECT_THAT(vec, ::testing::IsEmpty());

// Compound matchers
EXPECT_CALL(mock, write(_, ::testing::SizeIs(::testing::Gt(0))));
EXPECT_CALL(mock, openStream(::testing::AllOf(::testing::Gt(0), ::testing::Le(96000))));
```

---

## Parameterized Tests

```cpp
// Test the same logic over multiple inputs
struct VolumeInput { int input; int expected; };

class VolumeClampTest : public ::testing::TestWithParam<VolumeInput> {};

TEST_P(VolumeClampTest, Clamp_ReturnsExpected) {
    AudioManager mgr(48000);
    mgr.setVolume(GetParam().input);
    EXPECT_EQ(mgr.getVolume(), GetParam().expected);
}

INSTANTIATE_TEST_SUITE_P(
    BoundaryValues,
    VolumeClampTest,
    ::testing::Values(
        VolumeInput{-1, 0},
        VolumeInput{0,  0},
        VolumeInput{50, 50},
        VolumeInput{100, 100},
        VolumeInput{101, 100}
    )
);
```

---

## Death Tests

```cpp
// Verify that invalid preconditions trigger assertion / abort
TEST(AudioManagerDeathTest, Constructor_ZeroSampleRate_Aborts) {
    EXPECT_DEATH(AudioManager mgr(0), "sampleRate > 0");
}

TEST(AudioManagerDeathTest, Constructor_NegativeSampleRate_Aborts) {
    EXPECT_DEBUG_DEATH(AudioManager mgr(-1), "");
}
```

Death tests use `_test` suffix in test suite name → gtest runs them in a subprocess.

---

## Test Doubles — When to Use Which

| Double | gmock class | Use when |
|---|---|---|
| **Spy** (partial mock) | `NiceMock<T>` | You care about a few calls; ignore the rest |
| **Strict mock** | `StrictMock<T>` | Any unexpected call = test failure |
| **Fake** | Hand-written class | Simulates a dependency with lightweight working logic (e.g. `FakeFilesystem`) |
| **Stub** | `EXPECT_CALL(..).WillRepeatedly(Return(x))` | Provides canned responses, no behavior verification |

---

## Characterization Tests (Legacy Code)

```cpp
// When you have no spec, write tests that document CURRENT behavior
// Goal: create a safety net before refactoring

TEST_F(LegacyAudioMixerTest, Mix_TwoChannelsSameFreq_CharacterizesCurrentOutput) {
    LegacyAudioMixer mixer;
    auto out = mixer.mix({channel_a_, channel_b_});
    // Record what it actually returns today — even if it's "wrong"
    EXPECT_EQ(out.size(), 512U);
    EXPECT_NEAR(out[0], -0.0072f, 0.001f);  // captured from actual run
}
```

---

## Code Coverage with lcov / gcovr

```cmake
# Add coverage flags when building for coverage
if(ENABLE_COVERAGE)
    target_compile_options(car_plugin PRIVATE --coverage -O0 -g)
    target_link_options(car_plugin    PRIVATE --coverage)
    target_compile_options(audio_manager_test PRIVATE --coverage -O0 -g)
    target_link_options(audio_manager_test    PRIVATE --coverage)
endif()
```

```bash
# Run tests + generate HTML report
cmake -B build -DENABLE_COVERAGE=ON -DBUILD_TESTS=ON
cmake --build build
ctest --test-dir build --output-on-failure

gcovr --root . \
      --exclude tests/ \
      --html-details coverage/index.html \
      --print-summary
```

---

## Prerequisites

- GCC 9+ or Clang 12+ toolchain installed.
- CMake 3.16+ on PATH.
- For cross-compilation: ARM/AArch64 sysroot or Android NDK r25+.
- `ninja` build tool recommended for faster builds.


## Step-by-Step Workflows

### Step 1: Add gtest / gmock to CMake
Use `FetchContent_Declare(googletest ...)` or `find_package(GTest REQUIRED)`.

### Step 2: Create the test fixture
Derive from `::testing::Test`; initialize shared state in `SetUp()`; release in `TearDown()`.

### Step 3: Write tests following AAA
Arrange (set up inputs) → Act (call the SUT) → Assert (verify with `EXPECT_*` / `ASSERT_*`).

### Step 4: Mock external dependencies
Write a mock class using `MOCK_METHOD(...)`; set expectations with `EXPECT_CALL(mock, Method(...))`.

### Step 5: Measure coverage
Build with `--coverage`; run tests; generate a report with `gcov` / `lcov`; target ≥ 80% for new code.


## Troubleshooting

- **`EXPECT_CALL` not triggered** — the mock method was not called with the expected arguments; use `::testing::_` (wildcard) to debug.
- **Test binary links but segfaults** — an `ASSERT_*` inside a non-void helper function causes undefined return; use `EXPECT_*` or return an `AssertionResult`.
- **Coverage report shows 0%** — ensure the test binary is linked with `--coverage`; run `lcov --capture` after `ctest`.
- **Death test hangs on Windows** — death tests use `fork()`; on Windows use `EXPECT_DEATH_IF_SUPPORTED` or refactor to avoid process exit testing.


## Pre-Commit Checklist

- [ ] Every test follows **Arrange → Act → Assert** structure.
- [ ] Test names follow `MethodName_StateUnderTest_ExpectedBehavior`.
- [ ] No production code changes in a test commit (unless fixing a bug exposed by a test).
- [ ] `StrictMock` used by default; `NiceMock` only when justified with a comment.
- [ ] Each test has exactly one reason to fail (single logical assertion).
- [ ] No sleep/timer dependencies — use fake clocks or inject time.
- [ ] Tests pass when run in any order (`--gtest_shuffle` to check).
- [ ] CMake uses `gtest_discover_tests()` — not manual `add_test()`.

---

## References

- [GoogleTest Documentation](https://google.github.io/googletest/)
- [GoogleMock Cookbook](https://google.github.io/googletest/gmock_cook_book.html)
- [GoogleTest Primer](https://google.github.io/googletest/primer.html)
- [C++ Unit Testing with Google Test (YouTube)](https://www.youtube.com/playlist?list=PL_dsdStdDXbo-zApdWB5XiF2aWpsIiZ5B)
