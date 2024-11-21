from homeassistant import config_entries
from homeassistant.core import callback
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
        return SIBOptionsFlow()


class SIBOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for SIB."""

    async def async_step_init(self, user_input=None):
        """Initial step of options flow."""
        _LOGGER.warn("async_step_init: List of sensors from Entry (after adding): %s", self.config_entry.options.get("binary_sensors", []))

        if user_input is not None:
            if user_input.get("add_binary_sensor"):
                # Transition to the step for adding a new binary_sensor
                return await self.async_step_add_binary_sensor()

            _LOGGER.warn("New list of sensors from Entry (in step init): %s", self.config_entry.options.get("binary_sensors", []))
            # Exit the options flow without changing data as this was done in the sub-steps
            #return self.async_create_entry(title="", data=self.data)
            return await self.async_step_init()

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
            sensors = self.config_entry.options.get("binary_sensors", [])
            sensors.append(
                {
                    "name": user_input["name"],
                    "address": user_input["address"]
                })
            #self.data['binary_sensors'] = sensors
            _LOGGER.warn("New list of sensors: %s", sensors)
            
            # Update the config entry with the new sensors list
            # The copy seems to be needed, I was only able to have a single
            # entity without it.
            #current_options = self.config_entry.options.copy()
            #current_options["binary_sensors"] = sensors
            self.hass.config_entries.async_update_entry(
                self.config_entry, options={
                    "binary_sensors": sensors
                },
            )

            # Trigger a reload of the integration to apply changes
            #await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            _LOGGER.warn("async_step_add_binary_sensor: New list of sensors from Entry (after adding): %s", self.config_entry.options.get("binary_sensors", []))

            # Return to the main options menu
            #return self.async_create_entry(title="", data={ "binary_sensors": sensors })
            return await self.async_step_init()

        return self.async_show_form(
            step_id="add_binary_sensor",
            data_schema=vol.Schema({
                vol.Required("name"): str,
                vol.Required("address"): int,
            }),
        )