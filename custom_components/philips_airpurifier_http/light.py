"""The purifier's light brightness as a dimmable light."""

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import LIGHT_BRIGHTNESS_LIST, PHILIPS_LIGHT_BRIGHTNESS
from .entity import PhilipsAirPurifierEntity

LIGHT = LightEntityDescription(
    key=PHILIPS_LIGHT_BRIGHTNESS, name="Light", icon="mdi:brightness-6"
)

# The purifier only takes these steps; 0 is off.
LEVELS = [level for level in LIGHT_BRIGHTNESS_LIST if level]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = entry.runtime_data
    if LIGHT.key in data.keys:
        async_add_entities([PhilipsAirPurifierLight(data.fan, LIGHT)])


class PhilipsAirPurifierLight(PhilipsAirPurifierEntity, LightEntity):
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    @property
    def is_on(self) -> bool | None:
        level = self._fan._light_brightness
        return None if level is None else int(level) > 0

    @property
    def brightness(self) -> int | None:
        level = self._fan._light_brightness
        return None if level is None else round(int(level) * 255 / 100)

    async def async_turn_on(self, **kwargs) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            percent = kwargs[ATTR_BRIGHTNESS] * 100 / 255
            level = min(LEVELS, key=lambda step: abs(step - percent))
        elif self.is_on:
            return
        else:
            level = LEVELS[-1]
        await self._fan.async_set_light_brightness(level)
        await self._async_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self._fan.async_set_light_brightness(0)
        await self._async_refresh()
