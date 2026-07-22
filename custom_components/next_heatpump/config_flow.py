"""Config flow for Next Heatpump."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import callback

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_SLAVE, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

CONF_SLAVE = "slave"


class NextConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Next Heatpump."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            def _check():
                # Lazy import here too
                from pymodbus.client import ModbusTcpClient
                client = ModbusTcpClient(
                    host=user_input[CONF_HOST], port=user_input[CONF_PORT]
                )
                connected = client.connect()
                client.close()
                return connected

            try:
                ok = await self.hass.async_add_executor_job(_check)
                if not ok:
                    errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"Next Heatpump ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): int,
                vol.Required(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NextOptionsFlow(config_entry)


class NextOptionsFlow(config_entries.OptionsFlow):
    """Allow reconfiguring scan interval after setup."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self._config_entry.data.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
