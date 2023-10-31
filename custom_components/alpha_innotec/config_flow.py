import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries, exceptions
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .controller_api import ControllerAPI
from .gateway_api import GatewayAPI

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required("gateway_ip", description="Please enter the IP address of your gateway."): str,
    vol.Required("gateway_password", description="Please enter the password of your gateway."): str,
    vol.Required("controller_ip", description="Please enter the IP address of your controller."): str,
    vol.Required("controller_username", description="The username for your controller."): str,
    vol.Required("controller_password", description="The password for your controller."): str
})


def validate_input(data: dict) -> dict:
    controller_api = ControllerAPI(data["controller_ip"], data["controller_username"], data["controller_password"])
    gateway_api = GatewayAPI(data['gateway_ip'], data['gateway_password'])

    try:
        controller_api.login()
        gateway_api.login()
        system_information = controller_api.system_information()

        return system_information
    except Exception as exception:
        _LOGGER.debug("Exception: %s", exception)
        raise CannotConnect


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Alpha Innotec."""

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

                return self.async_create_entry(title=system_information.get("name", "Alpha Innotec"), data=user_input)
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
