"""Platform for sensor integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.climate import ClimateEntity, ClimateEntityDescription, ClimateEntityFeature, HVACAction, \
    HVACMode
from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
)
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .controller_api import ControllerAPI, Thermostat
from .const import DOMAIN, MODULE_TYPE_SENSOR
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
        entities.append(AlphaHomeSensor(
            coordinator=coordinator,
            api=controller_api,
            name=thermostat.name,
            description=ClimateEntityDescription(""),
            thermostat=thermostat
        ))

    async_add_entities(entities)


class AlphaCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, controller_api: ControllerAPI, gateway_api: GatewayAPI):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Alpha Sensor",
            update_interval=timedelta(seconds=30),
        )

        self.controller_api = controller_api
        self.gateway_api = gateway_api

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            rooms = await self.hass.async_add_executor_job(self.gateway_api.all_modules)
            _LOGGER.debug("Rooms: %s", rooms)

            thermostats: list[Thermostat] = []

            try:
                for room_id in rooms:
                    room_module = rooms[room_id]
                    room = await self.hass.async_add_executor_job(self.controller_api.room_details, room_id)

                    current_temperature = None

                    for module_id in room_module['modules']:
                        module_details = await self.hass.async_add_executor_job(self.gateway_api.get_module_details, module_id)
                        if module_details is None:
                            continue

                        if module_details["type"] == MODULE_TYPE_SENSOR:
                            current_temperature = module_details["currentTemperature"]

                    thermostat = Thermostat(
                        identifier=room_id,
                        name=room['name'],
                        current_temperature=current_temperature,
                        desired_temperature=room.get('desiredTemperature'),
                        minimum_temperature=room.get('minTemperature'),
                        maximum_temperature=room.get('maxTemperature'),
                        cooling=room.get('cooling'),
                        cooling_enabled=room.get('coolingEnabled')
                    )

                    thermostats.append(thermostat)
            except Exception as exception:
                _LOGGER.exception("There is an exception: %s", exception)

            return thermostats

            return []
        except Exception as exception:
            raise exception


class AlphaHomeSensor(CoordinatorEntity, ClimateEntity):
    """Representation of a Sensor."""

    _attr_precision = 0.1
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
    )

    def __init__(self, coordinator, api: ControllerAPI, name, description, thermostat: Thermostat):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=thermostat.identifier)
        self.api = api
        self.entity_description = description
        self._attr_name = name
        self.thermostat = thermostat
        self._target_temperature = self.thermostat.desired_temperature
        self._current_temperature = self.thermostat.current_temperature

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self.thermostat.identifier)
            },
            name=self._attr_name,
            manufacturer="Alpha Home",
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return self.thermostat.identifier

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        current_thermostat = None

        for thermostat in self.coordinator.data:
            if thermostat.identifier == self.thermostat.identifier:
                current_thermostat = thermostat

        if not current_thermostat:
            return

        self._current_temperature = current_thermostat.current_temperature
        self._target_temperature = current_thermostat.desired_temperature

        self.thermostat = current_thermostat

        self.async_write_ha_state()

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self.hass.async_add_executor_job(self.api.set_temperature, self.thermostat.identifier, temp)
            self._target_temperature = temp

    @property
    def hvac_action(self) -> HVACAction | None:
        if not self.thermostat.cooling_enabled:
            return None

        if self.thermostat.cooling:
            return HVACAction.COOLING

        return HVACAction.HEATING

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
