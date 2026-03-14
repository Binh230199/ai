/**
 * @file   good_temperature_sensor.hpp
 * @brief  GOOD example — Modern C++14 class following SOLID + RAII.
 *
 * @details
 *   Demonstrates:
 *    - Single Responsibility: reads temperature only
 *    - Dependency Inversion: depends on IAdcDriver abstraction
 *    - Rule of Five (resource managing class)
 *    - RAII via unique_ptr
 *    - [[nodiscard]] on factory and error-returning methods
 *    - Explicit constructor, fixed-width types
 *    - Doxygen on every public symbol
 *
 * @author  Example Author
 * @date    2026-03-14
 */

#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <stdexcept>

namespace Automotive::Sensor {

// ---------------------------------------------------------------------------
// Abstraction — depends on this, not on concrete AdcDriver
// ---------------------------------------------------------------------------

/**
 * @brief  Abstract ADC channel reader.
 * @thread_safety  Implementations must state their thread-safety contract.
 */
class IAdcDriver {
public:
    virtual ~IAdcDriver() = default;

    /**
     * @brief  Read a raw sample from the given channel.
     * @param[in] channel  ADC channel index (0–7).
     * @return Raw 12-bit sample (0–4095), or std::nullopt on hardware error.
     */
    [[nodiscard]] virtual std::optional<std::uint16_t>
        readChannel(std::uint8_t channel) const = 0;
};

// ---------------------------------------------------------------------------
// TemperatureSensor — Single Responsibility: NTC temperature measurement
// ---------------------------------------------------------------------------

/**
 * @brief  RAII handle to an NTC thermistor connected to an ADC channel.
 *
 * @details
 *   Converts raw ADC counts to degrees Celsius using a linear approximation.
 *   Inject a mock IAdcDriver in unit tests for full isolation.
 *
 * @thread_safety
 *   readDegC() is safe for concurrent callers after construction.
 *   Construction/destruction must not be concurrent with any other operation.
 */
class TemperatureSensor {
public:
    /**
     * @brief  Construct and bind to the given ADC channel.
     * @param[in] driver   ADC driver (injected — never null).
     * @param[in] channel  ADC channel index (0–7).
     * @throws std::invalid_argument if driver is null or channel > 7.
     */
    explicit TemperatureSensor(std::shared_ptr<IAdcDriver> driver,
                               std::uint8_t               channel);

    ~TemperatureSensor();

    // Non-copyable (unique hardware resource)
    TemperatureSensor(const TemperatureSensor&)            = delete;
    TemperatureSensor& operator=(const TemperatureSensor&) = delete;

    // Movable — transfers hardware ownership
    TemperatureSensor(TemperatureSensor&&)                 noexcept;
    TemperatureSensor& operator=(TemperatureSensor&&)      noexcept;

    /**
     * @brief  Read the current temperature.
     * @return Temperature in degrees Celsius, or std::nullopt on hardware error.
     */
    [[nodiscard]] std::optional<float> readDegC() const;

private:
    std::shared_ptr<IAdcDriver> m_driver;
    std::uint8_t                m_channel;

    static constexpr float         kTempMinDegC  {-40.0F};
    static constexpr float         kTempRangeDeg {165.0F};   // -40 to +125 °C
    static constexpr std::uint16_t kAdcFullScale  {4095U};

    [[nodiscard]] static float convertAdcToTemp(std::uint16_t raw) noexcept;
};

} // namespace Automotive::Sensor
