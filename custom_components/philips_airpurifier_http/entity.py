"""Entities that expose the purifier fan's extra controls and readings."""

from dataclasses import dataclass, field

from homeassistant.helpers.entity import Entity, EntityDescription

from .philips_airpurifier_fan import PhilipsAirPurifierFan


@dataclass
class PhilipsRuntimeData:
    """What a config entry's platforms share."""

    client: object
    fan: PhilipsAirPurifierFan
    # Status and filter keys the purifier reported at setup; entities for
    # features the model doesn't have (humidifier, wick filter) are skipped.
    keys: set[str] = field(default_factory=set)


class PhilipsAirPurifierEntity(Entity):
    """One feature of the purifier, shown on the same device as the fan.

    The fan polls the purifier; these entities read its state, get written
    whenever it updates, and send commands through its methods.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, fan: PhilipsAirPurifierFan, description: EntityDescription):
        self._fan = fan
        self.entity_description = description
        self._attr_unique_id = f"{fan.unique_id}_{description.key}"
        self._attr_device_info = fan.device_info

    @property
    def available(self) -> bool:
        return self._fan.available

    async def async_added_to_hass(self):
        self.async_on_remove(self._fan.async_add_listener(self.async_write_ha_state))

    async def _async_refresh(self):
        """Re-read the purifier after a command; listeners pick up the change."""
        await self._fan.async_update_ha_state(True)
