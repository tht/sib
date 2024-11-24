from copy import deepcopy
from typing import Any, Dict, Optional
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
import voluptuous as vol
import re
from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

class SIBConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for configuring an SIB instance."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # Try to configure an unique id, make sure it's actually unique (one instance per interface)
            await self.async_set_unique_id(f"{DOMAIN}_{user_input['interface']}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=f"SIB on {user_input['interface']} ({user_input['baud_rate']}bps)", data=user_input)

        # Show form when no user_input is supplied
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("interface", default="CAN0"): str,
                vol.Required("baud_rate", default=500000): int,
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return SIBOptionsFlow(config_entry)


# Custom validation function for the address field
def validate_topic_address(value):
    """Validate the address format."""
    if not isinstance(value, str):
        raise vol.Invalid("Address must be a string.")
    
    match = re.match(r"^(\d):(\d{1,3})$", value)
    if not match:
        raise vol.Invalid("Address must be in the format 'main:sub' where main=0-7 and sub=0-255.")
    
    x, y = int(match.group(1)), int(match.group(2))
    if not (0 <= x <= 7):
        raise vol.Invalid("main must be between 0 and 7.")
    if not (0 <= y <= 255):
        raise vol.Invalid("sub must be between 0 and 255.")
    
    return value


class SIBOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for SIB."""

    # Local cache for configuration to write it back at the very end
    data: Optional[Dict[str, Any]]

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Make a deepcopy of the existing options to work on"""
        self.data = deepcopy(config_entry.options.copy())
        _LOGGER.warn("config_flow.py/__init__: loaded configuration %s", self.data)
        #TODO: Make sure we have all the main keys (like `binary_sensors` set)

    async def async_step_init(self, user_input=None):
        """Initial step of options flow."""
        if user_input is not None:
            # Jump to sub-flow for choosen action
            if user_input.get("add_binary_sensor"):
                return await self.async_step_add_binary_sensor()
            if user_input.get("expose_binary_sensor"):
                return await self.async_step_expose_binary_sensor()

            # Exit the options flow and store working copy of data to Home-Assistant
            return self.async_create_entry(title="", data=self.data)

        # Show form when no user_input is supplied
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("add_binary_sensor", default=False): bool,
                vol.Optional("add_sensor", default=False): bool,
                vol.Optional("expose_binary_sensor", default=False): bool,
            }),
        )

    async def async_step_add_binary_sensor(self, user_input=None):
        """Step to add a new binary sensor."""
        if user_input is not None:
            # Validate the input (address and selected_entity)
            try:
                validated_address = validate_topic_address(user_input["address"])
            except vol.Invalid as e:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._build_schema(user_input),
                    errors={"address": str(e)}
                )

            # Add the new sensor
            self.data["binary_sensors"].append(
                {
                    "name": user_input["name"],
                    "address": user_input["address"],
                    "device_class": user_input['device_class']
                })

            # Return to the main options menu
            return await self.async_step_init()

        # Show form when no user_input is supplied
        device_class_options = [cls.value for cls in BinarySensorDeviceClass]
        return self.async_show_form(
            step_id="add_binary_sensor",
            data_schema=vol.Schema({
                vol.Required("name"): str,
                vol.Required("address"): str,
                vol.Required("device_class", default=self.config_entry.options.get("device_class", None)): vol.In(device_class_options),
            }),
        )

    async def async_step_expose_binary_sensor(self, user_input=None):
        """Step to add a new binary sensor."""
        if user_input is not None:
            # Add the new sensor
            self.data["binary_sensors"].append(
                {
                    "name": user_input["name"],
                    "address": user_input["address"],
                    "device_class": user_input['device_class']
                })

            # Return to the main options menu
            return await self.async_step_init()

        # Fetch all entities from the entity registry
        entity_registry = er.async_get(self.hass)
        entities = entity_registry.entities

        # Filter entities to include only those relevant to this integration
        integration_entities = {
            entity_id: entity
            for entity_id, entity in entities.items()
            if entity.platform != self.config_entry.domain and # Exclude own entities
                entity_id.startswith("binary_sensor.")         # and filter by matching type
        }

        options = {}
        for entity_id, entity in integration_entities.items():
            friendly_name = entity.original_name or entity_id  # Use entity_id if no friendly name
            options[entity_id] = f"{friendly_name} ({entity_id})"

        # Show form when no user_input is supplied
        return self.async_show_form(
            step_id="expose_binary_sensor",
            data_schema=vol.Schema({
                "address": user_input["address"],
                vol.Required("selected_entity", default=list(options.keys())[0]): vol.In(options),
            }),
        )