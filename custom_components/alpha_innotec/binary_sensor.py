"""Platform for binary sensor integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import UndefinedType
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator)

from .const import DOMAIN, MANUFACTURER
from .coordinator import AlphaInnotecCoordinator
from .gateway_api import GatewayAPI
from .structs.Valve import Valve

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the sensor platform."""

    _LOGGER.debug("Setting up binary sensors")

    coordinator = AlphaInnotecCoordinator(hass)

    await coordinator.async_config_entry_first_refresh()

    entities = []

    for valve in coordinator.data['valves']:
        entities.append(AlphaHomeBinarySensor(
            coordinator=coordinator,
            description=BinarySensorEntityDescription("", entity_registry_enabled_default=valve.used),
            valve=valve
        ))

    async_add_entities(entities)


class AlphaHomeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Binary Sensor."""

    def __init__(self, coordinator: AlphaInnotecCoordinator, description: BinarySensorEntityDescription, valve: Valve) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=valve.identifier)
        self.entity_description = description
        self.valve = valve

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self.valve.device_id)
            },
            name=self.valve.device_name,
            manufacturer=MANUFACTURER,
        )

    @property
    def name(self) -> str | UndefinedType | None:
        return self.valve.name

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return self.valve.identifier

    @property
    def is_on(self) -> bool | None:
        return self.valve.status

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        return BinarySensorDeviceClass.OPENING

    @callback
    def _handle_coordinator_update(self) -> None:
        for valve in self.coordinator.data['valves']:
            if valve.identifier == self.valve.identifier:
                self.valve = valve
                break

        _LOGGER.debug("Updating binary sensor: %s", self.valve.identifier)

        self.async_write_ha_state()
