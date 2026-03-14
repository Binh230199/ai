/**
 * @file   good_temperature_sensor.cpp
 * @brief  Implementation of TemperatureSensor — GOOD example.
 */

#include "good_temperature_sensor.hpp"

#include <stdexcept>
#include <utility>

namespace Automotive::Sensor {

// ---------------------------------------------------------------------------
// Constructor
// ---------------------------------------------------------------------------

TemperatureSensor::TemperatureSensor(std::shared_ptr<IAdcDriver> driver,
                                     std::uint8_t               channel)
    : m_driver{std::move(driver)}
    , m_channel{channel}
{
    if (!m_driver)         { throw std::invalid_argument{"TemperatureSensor: driver is null"}; }
    if (m_channel > 7U)    { throw std::invalid_argument{"TemperatureSensor: channel out of range"}; }
}

TemperatureSensor::~TemperatureSensor() = default;

TemperatureSensor::TemperatureSensor(TemperatureSensor&&) noexcept = default;

TemperatureSensor& TemperatureSensor::operator=(TemperatureSensor&&) noexcept = default;

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

std::optional<float> TemperatureSensor::readDegC() const
{
    const auto sample {m_driver->readChannel(m_channel)};
    if (!sample.has_value())
    {
        return std::nullopt;   // hardware error — caller decides how to handle
    }
    return convertAdcToTemp(*sample);
}

// ---------------------------------------------------------------------------
// Private helpers
// ---------------------------------------------------------------------------

float TemperatureSensor::convertAdcToTemp(std::uint16_t raw) noexcept
{
    // Linear: 0 counts → -40 °C, 4095 counts → 125 °C
    const float normalised {static_cast<float>(raw) / static_cast<float>(kAdcFullScale)};
    return kTempMinDegC + normalised * kTempRangeDeg;
}

} // namespace Automotive::Sensor
