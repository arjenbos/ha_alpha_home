"""Platform for sensor integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .base_coordinator import BaseCoordinator
from .const import DOMAIN, MANUFACTURER
from .controller_api import ControllerAPI, Thermostat
from .gateway_api import GatewayAPI

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""

    controller_api = hass.data[DOMAIN][entry.entry_id]['controller_api']
    gateway_api = hass.data[DOMAIN][entry.entry_id]['gateway_api']

    coordinator = AlphaCoordinator(hass, controller_api, gateway_api)

    await coordinator.async_config_entry_first_refresh()

    entities = []

    for thermostat in coordinator.data:
        entities.append(AlphaHomeBatterySensor(
            coordinator=coordinator,
            name=thermostat.name,
            description=SensorEntityDescription(""),
            thermostat=thermostat
        ))

    async_add_entities(entities)


class AlphaCoordinator(DataUpdateCoordinator, BaseCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, controller_api: ControllerAPI, gateway_api: GatewayAPI):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Alpha Sensor",
            update_interval=timedelta(seconds=30),
        )

        self.controller_api: ControllerAPI = controller_api
        self.gateway_api: GatewayAPI = gateway_api

    async def _async_update_data(self) -> list[Thermostat]:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        return await self.get_thermostats(self.hass, self.gateway_api, self.controller_api)


class AlphaHomeBatterySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator: AlphaCoordinator, name: str, description: SensorEntityDescription, thermostat: Thermostat) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=thermostat.identifier)
        self.entity_description = description
        self._attr_name = name
        self.thermostat = thermostat
        self._attr_native_value = thermostat.battery_percentage

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self.thermostat.identifier)
            },
            name=self._attr_name,
            manufacturer=MANUFACTURER,
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return self.thermostat.identifier
