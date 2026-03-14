/**
 * @file   good_sensor_read.c
 * @brief  GOOD example — defensive C function following MISRA C:2012 + project rules.
 *
 * @details
 *   Demonstrates:
 *    - Fixed-width types  (uint16_t, int16_t)
 *    - NULL-pointer guard at function entry
 *    - Module-initialisation guard
 *    - Named error enum return (never raw int)
 *    - Named constant instead of magic number
 *    - Single-responsibility function
 */

#include "sensor_driver.h"

#include <stdint.h>
#include <stdbool.h>

/* --------------------------------------------------------------------------
 * Module-private state
 * -------------------------------------------------------------------------- */
static bool s_isInitialised = false;

/* --------------------------------------------------------------------------
 * Private helpers
 * -------------------------------------------------------------------------- */

/**
 * @brief  Convert a raw 12-bit ADC reading to temperature in °C.
 *
 * @param[in] rawAdc  Raw ADC sample (0 – 4095).
 * @return Signed temperature value in degrees Celsius.
 */
static int16_t Convert_AdcToTemp(uint16_t rawAdc)
{
    /* Linear approximation: full-scale 4095 = 125 °C, 0 = -40 °C */
    static const int16_t K_TEMP_MIN_DEGC = -40;
    static const int16_t K_TEMP_RANGE    = 165;   /* 125 - (-40) */
    static const uint16_t K_ADC_FULLSCALE = 4095U;

    return (int16_t)(K_TEMP_MIN_DEGC
                     + (int16_t)((uint32_t)rawAdc
                                 * (uint32_t)K_TEMP_RANGE
                                 / K_ADC_FULLSCALE));
}

/* --------------------------------------------------------------------------
 * Public API
 * -------------------------------------------------------------------------- */

SensorError_t Sensor_Init(void)
{
    if (s_isInitialised)
    {
        return SENSOR_ERR_NOT_INIT;   /* idempotent guard */
    }

    /* Hardware initialisation (platform-specific) */
    Adc_Init(ADC_CHANNEL_NTC);

    s_isInitialised = true;
    return SENSOR_OK;
}

/**
 * @brief  Read the current temperature from the NTC sensor.
 *
 * @param[out] pTemperature_degC  Caller-allocated storage for result (°C).
 *                                Must not be NULL.
 * @return ::SensorError_t  SENSOR_OK on success, error code otherwise.
 *
 * @pre   Sensor_Init() must have returned SENSOR_OK.
 * @post  *pTemperature_degC is valid only when SENSOR_OK is returned.
 * @thread_safety  Safe for concurrent readers after successful init.
 */
SensorError_t Sensor_ReadTemperature(int16_t * const pTemperature_degC)
{
    /* Guard 1: NULL output pointer */
    if (pTemperature_degC == NULL)
    {
        return SENSOR_ERR_NULL_PTR;
    }

    /* Guard 2: module must be initialised */
    if (!s_isInitialised)
    {
        return SENSOR_ERR_NOT_INIT;
    }

    /* Read hardware — ADC_CHANNEL_NTC is a named constant, not a magic number */
    uint16_t rawAdc = Adc_ReadChannel(ADC_CHANNEL_NTC);

    *pTemperature_degC = Convert_AdcToTemp(rawAdc);

    return SENSOR_OK;
}
