/**
 * BAD EXAMPLE — C-style C++ anti-patterns. Violations annotated inline.
 * DO NOT use in production code.
 */

#include <string.h>   // BAD: C header; use <cstring> in C++

// BAD: no namespace — pollutes global namespace
// BAD: God class — reads sensor AND logs AND manages config in one class (violates SRP)
class Sensor {
public:
    // BAD: raw public pointer — no ownership semantics, no encapsulation
    int* handle;

    // BAD: plain int instead of fixed-width type
    int channel;

    // BAD: implicit conversion — missing 'explicit'
    Sensor(int ch) {
        channel = ch;
        // BAD: raw new — exception between here and assignment leaks
        handle = new int(ch);   // pretend this opens HW
    }

    // BAD: destructor defined but copy/move not — violates Rule of Five
    // copy will double-delete handle
    ~Sensor() {
        delete handle;   // BAD: no null check
    }

    // BAD: mixes responsibilities — sensor class doing logging
    void logTemperature() {
        printf("Temp: %d\n", *handle);   // BAD: C stdio in C++ code
    }

    // BAD: no [[nodiscard]] — caller can silently ignore the error
    // BAD: returns raw int as error code — no semantics
    int read(float* out) {
        // BAD: no null check on out pointer
        // BAD: magic numbers 100, 4096
        *out = *handle * 100.0f / 4096;
        return 0;
    }

    // BAD: static keyword used to "simulate" singleton with global state
    static Sensor* instance;   // raw singleton pointer, never deleted
};

Sensor* Sensor::instance {nullptr};  // global mutable state

// BAD: free function accessing object internals — breaks OOP encapsulation
void hackyReset(Sensor* s) {
    delete s->handle;          // bypasses class invariant
    s->handle = new int(0);
}
