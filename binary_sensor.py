"""Binary sensor platform for SIB."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.warn("binary_sensor.py async_setup_entry")
    """Set up SIB binary sensors from a config entry."""
    sensors = config_entry.options.get("binary_sensors", [])
    
    # Track existing entities to prevent duplicates
    #existing_entities = hass.data[DOMAIN].get(config_entry.entry_id, {}).get("binary_sensors", [])
    existing_entities = []
    _LOGGER.warn("Existing entities: %s", existing_entities)
    new_entities = []

    for sensor in sensors:
        if sensor not in existing_entities:
            _LOGGER.warn("New entity: %s", sensor)
            new_entities.append(SIBBinarySensor(config_entry, sensor["name"], sensor["address"], sensor["device_class"]))
            existing_entities.append(sensor)

    hass.data[DOMAIN][config_entry.entry_id]["binary_sensors"] = existing_entities

    # Add only the new entities
    async_add_entities(new_entities, update_before_add=True)


class SIBBinarySensor(BinarySensorEntity):
    """Representation of a SIB binary sensor."""

    def __init__(self, config_entry, name: str, address: str, device_class: str):
        """Initialize the binary sensor."""
        _LOGGER.warn("binary_sensor.py SIBBinarySensor.__init__")
        self._name = name
        self._address = address
        self._device_class = device_class
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{address}"
        self._attr_config_entry_id = config_entry.entry_id
        self._is_on = False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._is_on

    async def async_update(self):
        """Update the state of the sensor."""
        # For now, this is a dummy update. Replace with actual CAN logic later.
        self._is_on = not self._is_on