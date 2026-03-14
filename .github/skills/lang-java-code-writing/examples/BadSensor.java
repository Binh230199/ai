package com.automotive.sensor;

import android.content.Context;

/**
 * BAD EXAMPLE — common Java/Android anti-patterns. Violations annotated inline.
 * DO NOT use in production code.
 */
public class BadSensor {   // BAD: not final — implicitly designed for subclassing with no contract

    // BAD: static reference to Activity Context — memory leak
    public static Context sContext;

    // BAD: public mutable fields — no encapsulation; callers can corrupt state
    public int channel;
    public boolean isInit;

    // BAD: no @NonNull/@Nullable — unknown nullability contract
    // BAD: no parameter validation — null driver causes NPE later, far from the source
    public BadSensor(Object driver, int ch) {
        channel = ch;
        // BAD: driver stored without null check or type safety
    }

    // BAD: returns null — forces every caller to guess whether null is possible
    // BAD: no Javadoc, no @WorkerThread annotation
    public Float readTemp() {
        if (!isInit) return null;           // caller will get NPE if they forget to check

        try {
            // do work
            return 25.0f;
        } catch (Exception e) {
            // BAD: swallowed exception — failure is invisible
            return null;
        }
    }

    // BAD: performing I/O inline without thread annotation
    // BAD: catching generic Exception and swallowing it
    public void init() {
        try {
            Thread.sleep(500);   // BAD: blocking — will crash on main thread (NetworkOnMainThreadException equivalent)
            isInit = true;
        } catch (Exception e) {
            // BAD: silent swallow — init failure goes unnoticed
        }
    }

    // BAD: magic numbers 100, 4095 — undocumented, fragile
    private float convert(int raw) {
        return raw * 100.0f / 4095;
    }

    // BAD: Singleton via static mutable field — not thread-safe, leaks Context
    private static BadSensor sInstance;

    public static BadSensor getInstance(Context ctx) {
        if (sInstance == null) {              // BAD: not thread-safe — race condition
            sContext = ctx;                   // BAD: stores Activity context statically
            sInstance = new BadSensor(null, 0);
        }
        return sInstance;
    }
}
