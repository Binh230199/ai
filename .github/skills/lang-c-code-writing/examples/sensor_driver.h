/**
 * @file   sensor_driver.h
 * @brief  Public interface for the temperature sensor driver (GOOD example header).
 *
 * @details
 *   Demonstrates correct header structure:
 *    - Include guard with unique name
 *    - Doxygen @file block
 *    - Fixed-width types via <stdint.h>
 *    - Module error enum
 *    - Doxygen on every public symbol
 *    - Named constant for ADC channel
 *
 * @author  Example Author
 * @date    2026-03-14
 */

#ifndef SENSOR_DRIVER_H
#define SENSOR_DRIVER_H

#include <stdint.h>
#include <stdbool.h>

/* --------------------------------------------------------------------------
 * Constants
 * -------------------------------------------------------------------------- */

/** @brief ADC channel connected to the NTC thermistor. */
#define ADC_CHANNEL_NTC  (3U)

/* --------------------------------------------------------------------------
 * Error codes
 * -------------------------------------------------------------------------- */

/**
 * @brief  Return codes for the Sensor module.
 *
 * All public Sensor_* functions return one of these values.
 */
typedef enum
{
    SENSOR_OK            = 0,   /**< Operation completed successfully.      */
    SENSOR_ERR_NULL_PTR  = 1,   /**< Caller passed a NULL output pointer.   */
    SENSOR_ERR_NOT_INIT  = 2,   /**< Module not yet initialised.            */
    SENSOR_ERR_TIMEOUT   = 3,   /**< Hardware did not respond within limit. */
    SENSOR_ERR_HW_FAULT  = 4    /**< Unrecoverable hardware error detected. */
} SensorError_t;

/* --------------------------------------------------------------------------
 * Public API
 * -------------------------------------------------------------------------- */

/**
 * @brief  Initialise the temperature sensor module.
 *
 * @return ::SensorError_t  SENSOR_OK on success, error code otherwise.
 *
 * @pre   ADC hardware clock must be enabled by the BSP before this call.
 * @post  Sensor_ReadTemperature() may be called.
 * @thread_safety  Must be called from a single initialisation thread.
 */
SensorError_t Sensor_Init(void);

/**
 * @brief  Read the current temperature from the NTC sensor.
 *
 * @param[out] pTemperature_degC  Pointer to store the result in °C.
 *                                Must not be NULL.
 * @return ::SensorError_t  SENSOR_OK on success, error code otherwise.
 *
 * @pre   Sensor_Init() must have returned SENSOR_OK.
 * @post  *pTemperature_degC is valid only when SENSOR_OK is returned.
 * @thread_safety  Safe for concurrent readers after successful init.
 */
SensorError_t Sensor_ReadTemperature(int16_t * const pTemperature_degC);

/**
 * @brief  Deinitialise the sensor module and release hardware resources.
 *
 * @return ::SensorError_t  SENSOR_OK on success, error code otherwise.
 * @thread_safety  Must not be called concurrently with any other Sensor_* function.
 */
SensorError_t Sensor_Deinit(void);

#endif /* SENSOR_DRIVER_H */
