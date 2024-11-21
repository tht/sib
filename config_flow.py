from copy import deepcopy
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
import voluptuous as vol
from .const import DOMAIN

from typing import Optional, Dict, Any

import logging
_LOGGER = logging.getLogger(__name__)

class SIBConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SIB."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(f"{DOMAIN}_{user_input['interface']}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=f"SIB on {user_input['interface']} ({user_input['baud_rate']}bps)", data=user_input)

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


class SIBOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for SIB."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
        self.data = deepcopy(self.config_entry.options.get("binary_sensors", []))

    async def async_step_init(self, user_input=None):
        """Initial step of options flow."""
        _LOGGER.warn("async_step_init: List of sensors from Entry (after adding): %s", self.config_entry.options.get("binary_sensors", []))

        if user_input is not None:
            if user_input.get("add_binary_sensor"):
                # Transition to the step for adding a new binary_sensor
                return await self.async_step_add_binary_sensor()

            _LOGGER.warn("New list of sensors from Entry (in step init): %s", self.config_entry.options.get("binary_sensors", []))
            # Exit the options flow without changing data as this was done in the sub-steps
            return self.async_create_entry(title="", data={"binary_sensors": self.data})
            #return await self.async_step_init()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("add_binary_sensor", default=False): bool,
                vol.Optional("add_sensor", default=False): bool,
            }),
        )

    async def async_step_add_binary_sensor(self, user_input=None):
        """Step to add a new binary sensor."""
        if user_input is not None:
            # Add the new sensor
            #sensors = self.config_entry.options.get("binary_sensors", [])
            self.data.append(
                {
                    "name": user_input["name"],
                    "address": user_input["address"],
                    "device_class": user_input['device_class']
                })
            #self.data['binary_sensors'] = sensors
            _LOGGER.warn("New list of sensors: %s", self.data)
            
            _LOGGER.warn("async_step_add_binary_sensor: New list of sensors from Entry (after adding): %s", self.config_entry.options.get("binary_sensors", []))

            # Return to the main options menu
            #return self.async_create_entry(title="", data={ "binary_sensors": sensors })
            return await self.async_step_init()

        device_class_options = [cls.value for cls in BinarySensorDeviceClass]

        return self.async_show_form(
            step_id="add_binary_sensor",
            data_schema=vol.Schema({
                vol.Required("name"): str,
                vol.Required("address"): int,
                vol.Required("device_class", default=self.config_entry.options.get("device_class", None)): vol.In(device_class_options),
            }),
        )