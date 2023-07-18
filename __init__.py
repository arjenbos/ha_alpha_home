import logging

from .api import ControllerApi
from .const import DOMAIN, PLATFORMS

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Alpha Home from config entry."""
    _LOGGER.info("Setting up Alpha Home component")

    controller_api = ControllerApi(entry.data['controller_ip'], entry.data['username'], entry.data['password'])

    controller_api = await hass.async_add_executor_job(controller_api.login)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller_api

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Alpha Home config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
