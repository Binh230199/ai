package com.automotive.sensor.data

import com.automotive.sensor.ui.SensorRepository

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext

import javax.inject.Inject

/**
 * Production implementation of [SensorRepository].
 *
 * All methods are main-safe: they switch to [ioDispatcher] internally.
 * Callers may invoke from any thread, including [Dispatchers.Main].
 *
 * @param driver Low-level ADC driver interface.
 * @param ioDispatcher Dispatcher used for hardware I/O. Injected for testability.
 */
class SensorRepositoryImpl @Inject constructor(
    private val driver: IAdcDriver,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO // GOOD: injected
) : SensorRepository {

    /**
     * Reads the current temperature once.
     *
     * @param channel ADC channel index in range 0–7.
     * @return [Result.success] with °C value, or [Result.failure] on hardware error.
     * @throws IllegalArgumentException if [channel] is outside 0–7.
     */
    override suspend fun readDegC(channel: Int): Result<Float> {
        require(channel in 0..7) { "channel must be 0–7, got $channel" }
        return withContext(ioDispatcher) {           // GOOD: main-safe via withContext
            runCatching { driver.readChannel(channel) }
        }
    }

    /**
     * Emits temperature every [intervalMs] milliseconds as a cold [Flow].
     *
     * The flow is cold — it starts polling only when collected, and stops when cancelled.
     *
     * @param channel ADC channel index in range 0–7.
     * @param intervalMs Polling interval in milliseconds. Defaults to 1 000 ms.
     * @return Cold [Flow] of temperature readings in °C.
     */
    override fun temperatureStream(channel: Int, intervalMs: Long): Flow<Float> = flow {
        require(channel in 0..7) { "channel must be 0–7" }
        while (true) {
            runCatching { driver.readChannel(channel) }
                .onSuccess { emit(it) }
                // GOOD: don't crash the stream on a single transient read failure
            delay(intervalMs)
        }
    }.flowOn(ioDispatcher)                          // GOOD: upstream on IO, collector unchanged
}

// ---------- Domain interface (lives in domain module) ----------

interface SensorRepository {
    /** @see SensorRepositoryImpl.readDegC */
    suspend fun readDegC(channel: Int): Result<Float>

    /** @see SensorRepositoryImpl.temperatureStream */
    fun temperatureStream(channel: Int, intervalMs: Long = 1_000L): Flow<Float>
}

// Injected hardware driver interface — testable
interface IAdcDriver {
    fun readChannel(channel: Int): Float
}
