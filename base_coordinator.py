"""Platform for sensor integration."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

from . import GatewayAPI
from .const import MODULE_TYPE_SENSOR
from .controller_api import ControllerAPI
from .structs.Thermostat import Thermostat

_LOGGER = logging.getLogger(__name__)


class BaseCoordinator:
    async def get_thermostats(self, hass: HomeAssistant, gateway_api: GatewayAPI, controller_api: ControllerAPI):
        try:
            rooms = await hass.async_add_executor_job(gateway_api.all_modules)
            _LOGGER.debug("Rooms: %s", rooms)

            thermostats: list[Thermostat] = []

            db_modules = await hass.async_add_executor_job(gateway_api.db_modules)

            try:
                for room_id in rooms:
                    room_module = rooms[room_id]
                    room = await hass.async_add_executor_job(controller_api.room_details, room_id)

                    current_temperature = None
                    battery_percentage = None

                    for module_id in room_module['modules']:
                        if module_id not in db_modules['modules']:
                            continue

                        module_details = db_modules['modules'][module_id]

                        if module_details["type"] == MODULE_TYPE_SENSOR:
                            current_temperature = module_details["currentTemperature"]
                            battery_percentage = module_details["battery"]

                    thermostat = Thermostat(
                        identifier=room_id,
                        name=room['name'],
                        current_temperature=current_temperature,
                        desired_temperature=room.get('desiredTemperature'),
                        minimum_temperature=room.get('minTemperature'),
                        maximum_temperature=room.get('maxTemperature'),
                        cooling=room.get('cooling'),
                        cooling_enabled=room.get('coolingEnabled'),
                        battery_percentage=battery_percentage
                    )

                    thermostats.append(thermostat)
            except Exception as exception:
                _LOGGER.exception("There is an exception: %s", exception)

            return thermostats
        except Exception as exception:
            raise exception
