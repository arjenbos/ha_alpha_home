import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries, exceptions
from homeassistant.data_entry_flow import FlowResult

from . import ControllerApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required("controller_ip", description="Please enter the IP address of your controller."): str,
    vol.Required("username", description="The username for your controller."): str,
    vol.Required("password", description="The password for your controller."): str
})


def validate_input(data: dict):
    controller_api = ControllerApi(data["controller_ip"], data["username"], data["password"])
    try:
        controller_api.login()
        system_information = controller_api.system_information()
    except Exception:
        raise CannotConnect

    return system_information


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Alpha Home."""

    VERSION = 1

    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Invoke when a user initiates a flow via the user interface."""

        errors = {}

        if user_input is not None:
            try:
                system_information = await self.hass.async_add_executor_job(validate_input, user_input)

                return self.async_create_entry(title=system_information.get("name", "Alpha Home"), data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
