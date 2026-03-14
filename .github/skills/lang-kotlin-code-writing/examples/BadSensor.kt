package com.automotive.sensor

import android.app.Activity
import android.util.Log
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.launch

// ─────────────────────────────────────────────
// BAD EXAMPLES — annotated anti-patterns
// ─────────────────────────────────────────────

// BAD: static Activity reference → Context leak; Activity never garbage-collected
object BadSensorManager {
    var activity: Activity? = null     // BAD: static mutable reference to Context

    // BAD: GlobalScope — outlives any component; never cancelled
    fun startPolling() {
        GlobalScope.launch {           // BAD: use viewModelScope / lifecycleScope instead
            while (true) {
                val raw = readRaw()
                activity?.runOnUiThread {
                    // BAD: direct UI manipulation from a leaked context
                    Log.d("Sensor", "temp=$raw")
                }
            }
        }
    }

    private fun readRaw(): Float = 0f
}

// BAD: public mutable data class — callers can mutate state freely
data class BadSensorState(
    var tempDegC: Float,               // BAD: should be val
    var errorMessage: String?          // BAD: should be val; nullable without domain meaning
)

// BAD: function that can return null with no documentation and no alternative
class BadSensorReader {

    // BAD: returns null on error — callers must guess when and why
    fun readTemperature(channel: Int): Float? {
        if (channel < 0) return null   // BAD: null for error; use Result<Float> or throw
        return 25.0f
    }

    // BAD: !! operator — will crash if readTemperature returns null
    fun printTemperature() {
        val temp = readTemperature(-1)!!   // BAD: NullPointerException at runtime
        println(temp)
    }

    // BAD: blocking call with no coroutine / dispatcher — will ANR on main thread
    fun fetchFromServer(): String {
        Thread.sleep(5_000)            // BAD: blocking; use suspend + withContext(Dispatchers.IO)
        return "result"
    }

    // BAD: exception swallowed silently — caller never knows it failed
    fun safeRead(): Float {
        return try {
            readTemperature(0)!!
        } catch (e: Exception) {
            // BAD: swallowing exceptions hides bugs
            0f
        }
    }
}

// BAD: magic numbers directly in logic
class BadCalibrator {
    fun convert(raw: Int): Float {
        return raw * 0.0625f + 2.5f    // BAD: magic numbers; use named constants
    }

    companion object {
        // BAD: mutable singleton state — not thread-safe, not testable
        var instance: BadCalibrator? = null
        fun get(): BadCalibrator {
            if (instance == null) {
                instance = BadCalibrator() // BAD: not thread-safe; use Hilt @Singleton
            }
            return instance!!              // BAD: !! again
        }
    }
}
