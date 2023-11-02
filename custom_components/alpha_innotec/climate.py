"""Platform for sensor integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.climate import (ClimateEntity,
                                              ClimateEntityDescription,
                                              ClimateEntityFeature, HVACAction,
                                              HVACMode)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import UndefinedType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .controller_api import ControllerAPI, Thermostat
from .coordinator import AlphaInnotecCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the sensor platform."""

    _LOGGER.debug("Setting up climate sensors")

    coordinator = AlphaInnotecCoordinator(hass)

    await coordinator.async_config_entry_first_refresh()

    entities = []

    for thermostat in coordinator.data['thermostats']:
        entities.append(AlphaInnotecClimateSensor(
            coordinator=coordinator,
            description=ClimateEntityDescription(""),
            thermostat=thermostat
        ))

    async_add_entities(entities)


class AlphaInnotecClimateSensor(CoordinatorEntity, ClimateEntity):
    """Representation of a Sensor."""

    _attr_precision = 0.1
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
    )

    def __init__(self, coordinator: AlphaInnotecCoordinator, description: ClimateEntityDescription, thermostat: Thermostat) -> None:
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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for thermostat in self.coordinator.data['thermostats']:
            if thermostat.identifier == self.thermostat.identifier:
                self.thermostat = thermostat

        _LOGGER.debug("Updating climate sensor: %s", self.thermostat.identifier)

        self.async_write_ha_state()


    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.thermostat.current_temperature if isinstance(self.thermostat.current_temperature, (float, int)) else None

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        return self.thermostat.desired_temperature if isinstance(self.thermostat.desired_temperature, (float, int)) else None

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self.hass.async_add_executor_job(self.coordinator.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]['controller_api'].set_temperature, self.thermostat.identifier, temp)
            self.thermostat.desired_temperature = temp

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current hvac mode."""
        return HVACMode.AUTO

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac modes."""

        return [
            HVACMode.AUTO
        ]
