"""The purifier's readings and filter life as sensors."""

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    PHILIPS_ALLERGEN_INDEX,
    PHILIPS_HUMIDITY,
    PHILIPS_PM25,
    PHILIPS_TEMPERATURE,
    PHILIPS_TIMER_REMAINING,
    PHILIPS_WATER_LEVEL,
)
from .entity import PhilipsAirPurifierEntity
from .philips_airpurifier_fan import PhilipsAirPurifierFan


@dataclass(frozen=True, kw_only=True)
class PhilipsSensorDescription(SensorEntityDescription):
    value_fn: Callable[[PhilipsAirPurifierFan], object]


def _filter(key, name, value_fn):
    return PhilipsSensorDescription(
        key=key,
        name=name,
        icon="mdi:air-filter",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=value_fn,
    )


SENSORS = [
    PhilipsSensorDescription(
        key=PHILIPS_PM25,
        name="PM2.5",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda fan: fan._pm25,
    ),
    PhilipsSensorDescription(
        key=PHILIPS_ALLERGEN_INDEX,
        name="Allergen index",
        icon="mdi:flower-pollen",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda fan: fan._allergen_index,
    ),
    PhilipsSensorDescription(
        key=PHILIPS_TEMPERATURE,
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda fan: fan._temperature,
    ),
    PhilipsSensorDescription(
        key=PHILIPS_HUMIDITY,
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda fan: fan._humidity,
    ),
    PhilipsSensorDescription(
        key=PHILIPS_WATER_LEVEL,
        name="Water level",
        icon="mdi:water",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda fan: fan._water_level,
    ),
    PhilipsSensorDescription(
        key=PHILIPS_TIMER_REMAINING,
        name="Off timer remaining",
        icon="mdi:timer-sand",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda fan: fan._timer_remaining,
    ),
    _filter("fltsts0", "Pre-filter", lambda fan: fan._pre_filter),
    _filter("fltsts1", "HEPA filter", lambda fan: fan._hepa_filter),
    _filter("fltsts2", "Carbon filter", lambda fan: fan._carbon_filter),
    _filter("wicksts", "Wick filter", lambda fan: fan._wick_filter),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = entry.runtime_data
    async_add_entities(
        PhilipsAirPurifierSensor(data.fan, description)
        for description in SENSORS
        if description.key in data.keys
    )


class PhilipsAirPurifierSensor(PhilipsAirPurifierEntity, SensorEntity):
    entity_description: PhilipsSensorDescription

    @property
    def native_value(self):
        return self.entity_description.value_fn(self._fan)
