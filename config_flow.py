from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

class VanCANConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VanCAN."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(user_input["interface"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="VanCAN on " + user_input["interface"], data=user_input)

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
        return VanCANOptionsFlow()

class VanCANOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for VanCAN."""

    async def async_step_init(self, user_input=None):
        """Initial step of options flow."""
        if user_input is not None:
            if user_input.get("add_sensor"):
                # Transition to the step for adding a new sensor
                return await self.async_step_add_sensor()
            # Save changes and exit the options flow
            return self.async_create_entry(title="", data=self.config_entry.options)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("add_sensor", default=False): bool,
            }),
        )

    async def async_step_add_sensor(self, user_input=None):
        """Step to add a new sensor."""
        if user_input is not None:
            # Add the new sensor
            sensors = self.config_entry.options.get("sensors", [])
            sensors.append(
                {
                    "name": user_input["name"],
                    "address": user_input["address"]
                })
            
            # Update the config entry with the new sensors list
            self.hass.config_entries.async_update_entry(
                self.config_entry, options={"sensors": sensors},
            )

            # Trigger a reload of the integration to apply changes
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            # Return to the main options menu
            return await self.async_step_init()

        return self.async_show_form(
            step_id="add_sensor",
            data_schema=vol.Schema({
                vol.Required("name"): str,
                vol.Required("address"): int,
            }),
        )