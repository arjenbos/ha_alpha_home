import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import ControllerAPI, GatewayAPI
from .const import DOMAIN, MODULE_TYPE_SENSOR
from .structs.Thermostat import Thermostat
from .structs.Valve import Valve

_LOGGER = logging.getLogger(__name__)


class AlphaInnotecCoordinator(DataUpdateCoordinator):

    data: dict[str, list[Valve | Thermostat]]

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Alpha Innotec",
            update_interval=timedelta(seconds=60),
        )

        self.controller_api = hass.data[DOMAIN][self.config_entry.entry_id]['controller_api']
        self.gateway_api = hass.data[DOMAIN][self.config_entry.entry_id]['gateway_api']

    async def _async_update_data(self) -> dict[str, list[Valve | Thermostat]]:
        db_modules: dict = await self.hass.async_add_executor_job(self.gateway_api.db_modules)
        all_modules: dict = await self.hass.async_add_executor_job(self.gateway_api.all_modules)
        room_list: dict = await self.hass.async_add_executor_job(self.controller_api.room_list)

        thermostats: list[Thermostat] = []
        valves: list[Valve] = []

        for room_id in all_modules:
            room_module = all_modules[room_id]
            room = await self.hass.async_add_executor_job(self.controller_api.room_details, room_id, room_list)

            current_temperature = None
            battery_percentage = None

            for module_id in room_module['modules']:
                if module_id not in db_modules['modules']:
                    continue

                module_details = db_modules['modules'][module_id]

                if module_details["type"] == MODULE_TYPE_SENSOR:
                    current_temperature = module_details["currentTemperature"]
                    battery_percentage = module_details["battery"]

            if room.get('status', 'problem') == 'problem':
                _LOGGER.error("According to the API there is a problem with: %s", room['name'])

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

        for module_id in db_modules["modules"]:
            module = db_modules["modules"][module_id]

            if module["productId"] != 3:
                continue

            for instance in module["instances"]:
                valve_id = '0' + instance['instance'] + module['deviceid'][2:]

                used = False

                for room_id in all_modules:
                    if used is not True:
                        used = valve_id in all_modules[room_id]["modules"]

                valve = Valve(
                    identifier=valve_id,
                    name=module["name"] + '-' + instance['instance'],
                    instance=instance["instance"],
                    device_id=module["deviceid"],
                    device_name=module["name"],
                    status=instance["status"],
                    used=used
                )

                valves.append(valve)

        return {
            'valves': valves,
            'thermostats': thermostats
        }
