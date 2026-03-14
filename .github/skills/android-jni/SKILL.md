---
name: android-jni
description: >
  Use when writing, reviewing, or debugging JNI (Java Native Interface) code
  that bridges Android Java/Kotlin and C/C++ native code. Covers function naming
  conventions, JNI type mappings, local and global references, string and array
  handling, exception propagation, threading with JavaVM, and JNI_OnLoad setup.
argument-hint: <class-or-method> [write|review|debug]
---

# Android JNI — Java Native Interface

Practices for writing correct, safe JNI code in Android NDK projects targeting
**Android Automotive OS (AAOS)**.

Source of truth: [Android JNI Tips](https://developer.android.com/training/articles/perf-jni)
and the [JNI specification](https://docs.oracle.com/javase/8/docs/technotes/guides/jni/spec/jniTOC.html).

---

## When to Use This Skill

- Implementing `native` methods declared in Java or Kotlin.
- Reading/writing Java objects, strings, and arrays from C++.
- Calling Java methods from C++ (callbacks, listeners).
- Handling exceptions across the JNI boundary.
- Using JNI from background C++ threads.

---

## Function Naming Convention

JNI functions are resolved by name. The pattern is:

```
Java_<fully_qualified_class_name_with_dots_replaced_by_underscores>_<methodName>
```

```java
// Java/Kotlin declaration
package com.example.audio;

public class AudioEngine {
    public native int initialize(int sampleRate);
    public native void shutdown();
    public static native String getVersion();
}
```

```cpp
// C++ implementation — names must match exactly
#include <jni.h>

// Instance method
extern "C" JNIEXPORT jint JNICALL
Java_com_example_audio_AudioEngine_initialize(JNIEnv* env, jobject thiz, jint sampleRate) {
    // thiz = the Java AudioEngine instance
    return 0;
}

// Instance method, no params
extern "C" JNIEXPORT void JNICALL
Java_com_example_audio_AudioEngine_shutdown(JNIEnv* env, jobject thiz) {
}

// Static method — second param is jclass, not jobject
extern "C" JNIEXPORT jstring JNICALL
Java_com_example_audio_AudioEngine_getVersion(JNIEnv* env, jclass clazz) {
    return env->NewStringUTF("1.0.0");
}
```

**Rules:**
- `extern "C"` prevents C++ name mangling — required.
- `JNIEXPORT` and `JNICALL` are required macros from `<jni.h>`.
- `JNIEnv*` is per-thread and must NOT be shared or stored across threads. Use `JavaVM` for cross-thread access (see below).

---

## JNI Type Mappings

| Java type | JNI type | C type |
|---|---|---|
| `boolean` | `jboolean` | `uint8_t` |
| `byte` | `jbyte` | `int8_t` |
| `char` | `jchar` | `uint16_t` |
| `short` | `jshort` | `int16_t` |
| `int` | `jint` | `int32_t` |
| `long` | `jlong` | `int64_t` |
| `float` | `jfloat` | `float` |
| `double` | `jdouble` | `double` |
| `void` | `void` | `void` |
| `String` | `jstring` | — |
| `Object` | `jobject` | — |
| `Class` | `jclass` | — |
| `int[]` | `jintArray` | — |
| `byte[]` | `jbyteArray` | — |
| `Object[]` | `jobjectArray` | — |

---

## Strings

```cpp
// Java String → C string
extern "C" JNIEXPORT void JNICALL
Java_com_example_Foo_processName(JNIEnv* env, jobject thiz, jstring jName) {
    const char* name = env->GetStringUTFChars(jName, nullptr);
    if (name == nullptr) return;  // OOM — exception already thrown

    // Use name...
    LOGI("Name: %s", name);

    env->ReleaseStringUTFChars(jName, name);  // MUST release
}

// C string → Java String
extern "C" JNIEXPORT jstring JNICALL
Java_com_example_Foo_getDeviceName(JNIEnv* env, jclass clazz) {
    return env->NewStringUTF("AAOS Audio Device");
    // Returns nullptr (== null in Java) on OOM — caller should check
}
```

**Rule**: Every `GetStringUTFChars` must be paired with `ReleaseStringUTFChars`, even on error paths.

---

## Arrays

```cpp
// Read a Java byte[]
extern "C" JNIEXPORT jint JNICALL
Java_com_example_Foo_processBuffer(JNIEnv* env, jobject thiz, jbyteArray jBuffer) {
    jsize len = env->GetArrayLength(jBuffer);
    jbyte* buf = env->GetByteArrayElements(jBuffer, nullptr);
    if (buf == nullptr) return -1;  // exception thrown

    // Use buf[0..len-1] ...

    // JNI_ABORT = don't copy changes back to Java array (read-only use)
    // 0         = copy changes back (if you modified buf)
    env->ReleaseByteArrayElements(jBuffer, buf, JNI_ABORT);
    return len;
}

// Create and return a new byte[] to Java
extern "C" JNIEXPORT jbyteArray JNICALL
Java_com_example_Foo_getAudioData(JNIEnv* env, jobject thiz) {
    const std::vector<int8_t> data = getNativeAudioData();

    jbyteArray result = env->NewByteArray(static_cast<jsize>(data.size()));
    if (result == nullptr) return nullptr;  // OOM

    env->SetByteArrayRegion(result, 0, static_cast<jsize>(data.size()),
                            reinterpret_cast<const jbyte*>(data.data()));
    return result;
}
```

---

## Local and Global References

The JVM garbage-collects Java objects. JNI references keep them alive.

| Reference type | Scope | Created by | Freed by |
|---|---|---|---|
| **Local** | Current JNI call frame | Returned by most JNI calls | Automatically on method return; manually with `DeleteLocalRef` |
| **Global** | Until explicitly deleted | `NewGlobalRef` | `DeleteGlobalRef` (you MUST call this) |
| **Weak global** | Until GC collects the object | `NewWeakGlobalRef` | `DeleteWeakGlobalRef` |

```cpp
// Problem: storing a jobject for later use (e.g. callback reference)
static jobject g_listener = nullptr;  // WRONG — local ref goes stale after JNI call

// Correct: promote to global ref
extern "C" JNIEXPORT void JNICALL
Java_com_example_Foo_setListener(JNIEnv* env, jobject thiz, jobject listener) {
    if (g_listener != nullptr) {
        env->DeleteGlobalRef(g_listener);
    }
    g_listener = env->NewGlobalRef(listener);  // survives past the JNI call
}

// When done with the listener
void clearListener(JNIEnv* env) {
    if (g_listener != nullptr) {
        env->DeleteGlobalRef(g_listener);
        g_listener = nullptr;
    }
}
```

**Rule**: In loops that call JNI functions returning local refs, delete each local ref before the next iteration or you will exhaust the local reference table (default limit: 512 entries).

---

## Exception Handling

JNI exceptions are *pending* — they don't unwind the C++ stack. You must check for them explicitly.

```cpp
// After any JNI call that can throw
env->CallVoidMethod(obj, methodId, arg);
if (env->ExceptionCheck()) {
    env->ExceptionDescribe();  // prints to logcat
    env->ExceptionClear();     // clears the pending exception
    return;                    // or handle the error
}

// Throw a Java exception from C++
void throwJavaException(JNIEnv* env, const char* className, const char* message) {
    jclass exClass = env->FindClass(className);
    if (exClass != nullptr) {
        env->ThrowNew(exClass, message);
    }
}

// Usage
throwJavaException(env, "java/lang/IllegalArgumentException", "sampleRate must be > 0");
return -1;  // return immediately — exception is now pending in Java
```

**Rule**: Never let a pending Java exception remain while calling further JNI functions (except `ExceptionCheck`, `ExceptionOccurred`, `ExceptionDescribe`, `ExceptionClear`). The behavior is undefined.

---

## Calling Java Methods from C++

```cpp
// Cache jclass and jmethodID at JNI_OnLoad time — FindClass is expensive
static jclass    g_listenerClass  = nullptr;
static jmethodID g_onAudioReady   = nullptr;

// In JNI_OnLoad:
jclass localClass = env->FindClass("com/example/audio/IAudioListener");
g_listenerClass   = static_cast<jclass>(env->NewGlobalRef(localClass));
g_onAudioReady    = env->GetMethodID(g_listenerClass, "onAudioReady", "([BI)V");

// Call the Java method
void notifyAudioReady(JNIEnv* env, jobject listenerObj, jbyteArray data, jint length) {
    env->CallVoidMethod(listenerObj, g_onAudioReady, data, length);
}
```

**Method signature string format**: `(<param-types>)<return-type>`

| Type | Signature character |
|---|---|
| `int` | `I` |
| `long` | `J` |
| `boolean` | `Z` |
| `byte` | `B` |
| `void` | `V` |
| `String` | `Ljava/lang/String;` |
| `int[]` | `[I` |
| `Object` | `Ljava/lang/Object;` |

---

## Threading — JNIEnv from Background Threads

`JNIEnv*` is thread-local. A background native thread has no `JNIEnv*` by default.

```cpp
static JavaVM* g_jvm = nullptr;

// Store the JavaVM in JNI_OnLoad
JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    g_jvm = vm;
    JNIEnv* env;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK) {
        return JNI_ERR;
    }
    // Cache class/method IDs here while env is available
    return JNI_VERSION_1_6;
}

// In a background C++ thread:
void nativeThreadCallback() {
    JNIEnv* env = nullptr;
    bool attached = false;

    jint result = g_jvm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6);
    if (result == JNI_EDETACHED) {
        g_jvm->AttachCurrentThread(&env, nullptr);
        attached = true;
    }

    // Use env...
    env->CallVoidMethod(g_listener, g_onAudioReady, ...);

    if (attached) {
        g_jvm->DetachCurrentThread();
    }
}
```

**Rule**: Every `AttachCurrentThread` must be paired with `DetachCurrentThread` before the thread exits. Failing to detach causes the JVM to crash on thread exit.

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

### Step 1: Declare native methods in Java/Kotlin
Add `external` (Kotlin) or `native` (Java) methods; load with `System.loadLibrary("name")`.

### Step 2: Implement JNI functions in C/C++
Name them `Java_<pkg>_<class>_<method>(JNIEnv*, jclass, ...)`.

### Step 3: Map JNI types correctly
Use the JNI Type Mapping table below; convert `jstring` with `GetStringUTFChars` / `ReleaseStringUTFChars`.

### Step 4: Manage local references
Delete local refs in loops with `env->DeleteLocalRef()`; use global refs for long-lived objects.

### Step 5: Propagate exceptions
Check `env->ExceptionCheck()` after Java calls; throw with `env->ThrowNew()`.


## Troubleshooting

- **`UnsatisfiedLinkError`** — library name in `System.loadLibrary` must match `CMakeLists.txt` `add_library` name (without `lib` prefix or `.so` suffix).
- **JNI crash with no stack trace** — build with NDK debug symbols; use `ndk-stack` to symbolicate the tombstone.
- **Memory leak on local references** — local refs are not freed automatically in loops; call `env->DeleteLocalRef()` in the loop body.
- **`JNIEnv` not valid in a new thread** — attach the thread to the JVM with `jvm->AttachCurrentThread()`; detach before the thread exits.


## Pre-Commit Checklist

- [ ] All JNI function names exactly match `Java_<package>_<Class>_<method>`.
- [ ] `extern "C"` on every JNI function.
- [ ] Every `GetStringUTFChars` paired with `ReleaseStringUTFChars`.
- [ ] Every `GetByteArrayElements` etc. paired with its `Release*` call.
- [ ] Every `NewGlobalRef` paired with `DeleteGlobalRef` when no longer needed.
- [ ] Exception checked after every JNI call that can throw.
- [ ] No `JNIEnv*` stored as a global — stored `JavaVM*` instead.
- [ ] Every `AttachCurrentThread` paired with `DetachCurrentThread`.
- [ ] Method and field IDs cached in `JNI_OnLoad` — not looked up on every call.

---

## References

- [Android JNI Tips](https://developer.android.com/training/articles/perf-jni)
- [JNI Specification (Oracle)](https://docs.oracle.com/javase/8/docs/technotes/guides/jni/spec/jniTOC.html)
- [Android NDK Samples — hello-jni](https://github.com/android/ndk-samples/tree/main/hello-jni)
