"""Support for Phillips Air Purifiers and Humidifiers."""

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.fan import (
    PLATFORM_SCHEMA,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DEFAULT_NAME

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Import a YAML-configured purifier into a config entry."""
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={CONF_HOST: config[CONF_HOST], CONF_NAME: config[CONF_NAME]},
        )
    )
    ir.async_create_issue(
        hass,
        DOMAIN,
        "deprecated_yaml",
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the purifier fan from a config entry."""
    async_add_entities([entry.runtime_data.fan], True)
