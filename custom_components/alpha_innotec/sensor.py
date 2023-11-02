"""Platform for sensor integration."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import StateType, UndefinedType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .controller_api import Thermostat
from .coordinator import AlphaInnotecCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the sensor platform."""

    _LOGGER.debug("Setting up sensors")

    coordinator = AlphaInnotecCoordinator(hass)

    await coordinator.async_config_entry_first_refresh()

    entities = []

    for thermostat in coordinator.data["thermostats"]:
        entities.append(AlphaInnotecBatterySensor(
            coordinator=coordinator,
            description=SensorEntityDescription(""),
            thermostat=thermostat
        ))

    async_add_entities(entities)


class AlphaInnotecBatterySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator: AlphaInnotecCoordinator, description: SensorEntityDescription,
                 thermostat: Thermostat) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=thermostat.identifier)
        self.entity_description = description
        self.thermostat = thermostat

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self.thermostat.identifier)
            },
            name=self.thermostat.name,
            manufacturer=MANUFACTURER,
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return self.thermostat.identifier

    @property
    def name(self) -> str | UndefinedType | None:
        return self.thermostat.name

    @property
    def native_value(self):
        return self.thermostat.battery_percentage if isinstance(self.thermostat.battery_percentage, (float, int)) else None

    @callback
    def _handle_coordinator_update(self) -> None:
        for thermostat in self.coordinator.data['thermostats']:
            if thermostat.identifier == self.thermostat.identifier:
                self.thermostat = thermostat
                break

        _LOGGER.debug("Updating battery sensor: %s", self.thermostat.identifier)

        self.async_write_ha_state()
