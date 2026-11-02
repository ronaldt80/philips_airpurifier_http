"""The purifier's on/off settings as switches."""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import PHILIPS_CHILD_LOCK, PHILIPS_DISPLAY_LIGHT
from .entity import PhilipsAirPurifierEntity
from .philips_airpurifier_fan import PhilipsAirPurifierFan


@dataclass(frozen=True, kw_only=True)
class PhilipsSwitchDescription(SwitchEntityDescription):
    value_fn: Callable[[PhilipsAirPurifierFan], object]
    set_fn: Callable[[PhilipsAirPurifierFan, bool], Coroutine]


SWITCHES = [
    PhilipsSwitchDescription(
        key=PHILIPS_CHILD_LOCK,
        name="Child lock",
        icon="mdi:lock",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda fan: fan._child_lock,
        set_fn=lambda fan, on: fan.async_set_child_lock(on),
    ),
    PhilipsSwitchDescription(
        key=PHILIPS_DISPLAY_LIGHT,
        name="Display light",
        icon="mdi:monitor",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda fan: fan._display_light,
        set_fn=lambda fan, on: fan.async_set_display_light(on),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = entry.runtime_data
    async_add_entities(
        PhilipsAirPurifierSwitch(data.fan, description)
        for description in SWITCHES
        if description.key in data.keys
    )


class PhilipsAirPurifierSwitch(PhilipsAirPurifierEntity, SwitchEntity):
    entity_description: PhilipsSwitchDescription

    @property
    def is_on(self) -> bool | None:
        value = self.entity_description.value_fn(self._fan)
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs) -> None:
        await self.entity_description.set_fn(self._fan, True)
        await self._async_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.entity_description.set_fn(self._fan, False)
        await self._async_refresh()
