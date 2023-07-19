import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .controller_api import ControllerAPI
from .const import DOMAIN, PLATFORMS
from .gateway_api import GatewayAPI

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Alpha Home from config entry."""
    _LOGGER.debug("Setting up Alpha Home component")

    controller_api = ControllerAPI(entry.data['controller_ip'], entry.data['controller_username'], entry.data['controller_password'])
    controller_api = await hass.async_add_executor_job(controller_api.login)
    gateway_api = GatewayAPI(entry.data['gateway_ip'], entry.data['gateway_password'])
    gateway_api = await hass.async_add_executor_job(gateway_api.login)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "controller_api": controller_api,
        "gateway_api": gateway_api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Alpha Home config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
