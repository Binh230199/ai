package com.automotive.sensor;

import android.util.Log;

import androidx.annotation.AnyThread;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.annotation.WorkerThread;

import java.util.Objects;
import java.util.Optional;

/**
 * RAII-style temperature sensor backed by an injected {@link IAdcDriver}.
 *
 * <p>Demonstrates:
 * <ul>
 *   <li>Dependency injection via constructor (Dependency Inversion)</li>
 *   <li>Null safety with {@link NonNull}/{@link Nullable} and {@link Objects#requireNonNull}</li>
 *   <li>{@link Optional} as explicit "no value" return (no null APIs)</li>
 *   <li>Immutable fields ({@code final})</li>
 *   <li>Proper Javadoc with {@code @param}, {@code @return}, {@code @throws}</li>
 *   <li>Thread-safety annotations</li>
 *   <li>Single Responsibility: reads temperature only</li>
 * </ul>
 *
 * @thread_safety Safe for concurrent callers after successful {@link #init()}.
 */
public final class GoodTemperatureSensor {

    private static final String TAG = GoodTemperatureSensor.class.getSimpleName();

    // --- Constants -----------------------------------------------------------

    private static final float K_TEMP_MIN_DEG_C  = -40.0f;
    private static final float K_TEMP_RANGE_DEG  = 165.0f;   // -40 to +125 °C
    private static final int   K_ADC_FULL_SCALE  = 4095;

    // --- Fields --------------------------------------------------------------

    private final IAdcDriver mDriver;
    private final int        mChannel;
    private volatile boolean mIsInitialised;    // volatile: single-variable visibility

    // --- Constructor ---------------------------------------------------------

    /**
     * Constructs the sensor but does not open the hardware yet.
     *
     * @param driver  ADC driver implementation; must not be null.
     * @param channel ADC channel index (0–7).
     * @throws IllegalArgumentException if {@code channel} is out of range.
     */
    public GoodTemperatureSensor(@NonNull IAdcDriver driver, int channel) {
        mDriver  = Objects.requireNonNull(driver, "driver must not be null");
        if (channel < 0 || channel > 7) {
            throw new IllegalArgumentException("channel must be 0–7, got " + channel);
        }
        mChannel = channel;
    }

    // --- Public API ----------------------------------------------------------

    /**
     * Initialises the hardware. Must be called before {@link #readDegC()}.
     *
     * @return {@code true} on success, {@code false} if already initialised.
     * @throws SensorException if the hardware reports an error during init.
     */
    @WorkerThread
    public boolean init() throws SensorException {
        if (mIsInitialised) { return false; }
        try {
            mDriver.openChannel(mChannel);
        } catch (HalException e) {
            throw new SensorException("Failed to open ADC channel " + mChannel, e);
        }
        mIsInitialised = true;
        return true;
    }

    /**
     * Reads the current temperature.
     *
     * @return Temperature in degrees Celsius, or {@link Optional#empty()} on hardware error.
     * @throws IllegalStateException if {@link #init()} has not been called.
     */
    @WorkerThread
    @NonNull
    public Optional<Float> readDegC() {
        if (!mIsInitialised) {
            throw new IllegalStateException("GoodTemperatureSensor not initialised");
        }
        try {
            int raw = mDriver.readChannel(mChannel);
            return Optional.of(convertAdcToTemp(raw));
        } catch (HalException e) {
            Log.e(TAG, "readDegC failed: channel=" + mChannel, e);
            return Optional.empty();    // legitimate hardware failure — not a bug
        }
    }

    /**
     * Releases the hardware channel.
     */
    @WorkerThread
    public void close() {
        if (!mIsInitialised) { return; }
        mDriver.closeChannel(mChannel);
        mIsInitialised = false;
    }

    // --- Private helpers -----------------------------------------------------

    private static float convertAdcToTemp(int raw) {
        return K_TEMP_MIN_DEG_C + ((float) raw / K_ADC_FULL_SCALE) * K_TEMP_RANGE_DEG;
    }
}
