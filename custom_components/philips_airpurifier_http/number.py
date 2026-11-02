"""The purifier's off timer as a number."""

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import PHILIPS_TIMER
from .entity import PhilipsAirPurifierEntity

TIMER = NumberEntityDescription(
    key=PHILIPS_TIMER,
    name="Off timer",
    icon="mdi:timer-outline",
    native_min_value=0,
    native_max_value=12,
    native_step=1,
    native_unit_of_measurement=UnitOfTime.HOURS,
    mode=NumberMode.SLIDER,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = entry.runtime_data
    if TIMER.key in data.keys:
        async_add_entities([PhilipsAirPurifierTimer(data.fan, TIMER)])


class PhilipsAirPurifierTimer(PhilipsAirPurifierEntity, NumberEntity):
    @property
    def native_value(self) -> float | None:
        timer = self._fan._timer
        return None if timer is None else int(timer)

    async def async_set_native_value(self, value: float) -> None:
        await self._fan.async_set_timer(int(value))
        await self._async_refresh()
