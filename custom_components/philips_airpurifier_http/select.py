"""The purifier's multiple-choice settings as selects."""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    FUNCTION_MAP,
    PHILIPS_FUNCTION,
    PHILIPS_TARGET_HUMIDITY,
    PHILIPS_USED_INDEX,
    TARGET_HUMIDITY_LIST,
    USED_INDEX_MAP,
)
from .entity import PhilipsAirPurifierEntity
from .philips_airpurifier_fan import PhilipsAirPurifierFan


@dataclass(frozen=True, kw_only=True)
class PhilipsSelectDescription(SelectEntityDescription):
    value_fn: Callable[[PhilipsAirPurifierFan], object]
    set_fn: Callable[[PhilipsAirPurifierFan, str], Coroutine]


SELECTS = [
    PhilipsSelectDescription(
        key=PHILIPS_USED_INDEX,
        name="Displayed index",
        icon="mdi:gauge",
        entity_category=EntityCategory.CONFIG,
        options=list(USED_INDEX_MAP.values()),
        value_fn=lambda fan: fan._used_index,
        set_fn=lambda fan, option: fan.async_set_used_index(option),
    ),
    PhilipsSelectDescription(
        key=PHILIPS_FUNCTION,
        name="Function",
        icon="mdi:air-humidifier",
        options=list(FUNCTION_MAP.values()),
        value_fn=lambda fan: fan._function,
        set_fn=lambda fan, option: fan.async_set_function(option),
    ),
    PhilipsSelectDescription(
        key=PHILIPS_TARGET_HUMIDITY,
        name="Target humidity",
        icon="mdi:water-percent",
        options=[str(humidity) for humidity in TARGET_HUMIDITY_LIST],
        value_fn=lambda fan: fan._target_humidity,
        set_fn=lambda fan, option: fan.async_set_target_humidity(int(option)),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = entry.runtime_data
    async_add_entities(
        PhilipsAirPurifierSelect(data.fan, description)
        for description in SELECTS
        if description.key in data.keys
    )


class PhilipsAirPurifierSelect(PhilipsAirPurifierEntity, SelectEntity):
    entity_description: PhilipsSelectDescription

    @property
    def current_option(self) -> str | None:
        value = self.entity_description.value_fn(self._fan)
        if value is None or str(value) not in self.options:
            return None
        return str(value)

    async def async_select_option(self, option: str) -> None:
        await self.entity_description.set_fn(self._fan, option)
        await self._async_refresh()
