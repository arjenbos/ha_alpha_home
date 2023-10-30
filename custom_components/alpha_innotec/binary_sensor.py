"""Platform for binary sensor integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription, \
    BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import UndefinedType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, MANUFACTURER
from .gateway_api import GatewayAPI
from .structs.Valve import Valve

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""

    _LOGGER.debug("Setting up binary sensors")

    gateway_api = hass.data[DOMAIN][entry.entry_id]['gateway_api']

    coordinator = AlphaCoordinator(hass, gateway_api)

    await coordinator.async_config_entry_first_refresh()

    entities = []

    for valve in coordinator.data:
        entities.append(AlphaHomeBinarySensor(
            coordinator=coordinator,
            name=valve.name,
            description=BinarySensorEntityDescription(""),
            valve=valve
        ))

    async_add_entities(entities)


class AlphaCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, gateway_api: GatewayAPI):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Alpha Innotec Binary Coordinator",
            update_interval=timedelta(seconds=30),
        )

        self.gateway_api: GatewayAPI = gateway_api

    async def _async_update_data(self) -> list[Valve]:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """

        db_modules: dict = await self.hass.async_add_executor_job(self.gateway_api.db_modules)

        valves: list[Valve] = []

        for module_id in db_modules["modules"]:
            module = db_modules["modules"][module_id]

            if module["productId"] != 3:
                continue

            for instance in module["instances"]:
                valve = Valve(
                    identifier=module["deviceid"] + '-' + instance['instance'],
                    name=module["name"] + '-' + instance['instance'],
                    instance=instance["instance"],
                    device_id=module["deviceid"],
                    device_name=module["name"],
                    status=instance["status"]
                )

                valves.append(valve)

        _LOGGER.debug("Finished getting valves from API")

        return valves


class AlphaHomeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator: AlphaCoordinator, name: str, description: BinarySensorEntityDescription, valve: Valve) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=valve.identifier)
        self.entity_description = description
        self._attr_name = name
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
        return self._attr_name

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
