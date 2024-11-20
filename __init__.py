from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

import logging
_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up VanCAN from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "sensors": entry.options.get("sensors", []),  # Load sensors from options
    }

    _LOGGER.warn("Sensors loaded in __init__.py: %s", entry.options.get("sensors", []))

    # Forward entry setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["binary_sensor"])
    return True

async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "binary_sensor")
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok