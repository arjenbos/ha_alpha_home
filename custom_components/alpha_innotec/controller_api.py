import base64
import logging
import urllib
from urllib.parse import unquote

import requests

from .api import BaseAPI
from .structs.Thermostat import Thermostat

_LOGGER = logging.getLogger(__name__)


class ControllerAPI(BaseAPI):

    def call(self, endpoint: str, data: dict = None) -> dict:
        if data is None:
            data = {}

        _LOGGER.debug("[%s] - requesting", endpoint)
        json_response = None

        try:
            data['userid'] = self.user_id
            data['udid'] = self.udid
            data['reqcount'] = self.request_count

            post_data_sorted = sorted(data.items(), key=lambda val: val[0])

            urlencoded_body = urllib.parse.urlencode(post_data_sorted, encoding='utf-8')
            urlencoded_body_prepared_for_hash = self._prepare_request_body_for_hash(urlencoded_body)
            urlencoded_body_prepared_for_hash = urlencoded_body_prepared_for_hash.replace('&', '|')
            urlencoded_body_prepared_for_hash = urlencoded_body_prepared_for_hash + "|"

            request_signature = base64.b64encode(
                self.encode_signature(urlencoded_body_prepared_for_hash, self.device_token_decrypted)).decode()

            self.last_request_signature = request_signature

            urlencoded_body = urlencoded_body + "&" + urllib.parse.urlencode({"request_signature": request_signature},
                                                                             encoding='utf-8')

            _LOGGER.debug("[%s] - body: %s", endpoint, urlencoded_body)

            response = self.session.post("http://{hostname}/{endpoint}".format(hostname=self.api_host, endpoint=endpoint),
                                     data=urlencoded_body,
                                     headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
                                     )

            self.request_count = self.request_count + 1

            _LOGGER.debug("[%s] - response code: %s", endpoint, response.status_code)
            json_response = response.json()
        except Exception as exception:
            _LOGGER.exception("Unable to fetch data from API: %s", exception)

        _LOGGER.debug("[%s] - response body: %s", endpoint, json_response)

        if not json_response['success']:
            raise Exception('Failed to get data')
        else:
            _LOGGER.debug('[%s] - successfully fetched data from API', endpoint)

        return json_response

    def login(self):
        response = self.session.post("http://" + self.api_host + "/api/user/token/challenge", data={
            "udid": self.udid
        })

        _LOGGER.debug('[api/user/token/challenge] - response body: %s', response.json())

        device_token = response.json()['devicetoken']

        response = self.session.post("http://" + self.api_host + "/api/user/token/response", data={
            "login": self.username,
            "token": device_token,
            "udid": self.udid,
            "hashed": base64.b64encode(self.encode_signature(self.password, device_token)).decode()
        })

        _LOGGER.debug('[api/user/token/response] - response body: %s', response.json())

        if "devicetoken_encrypted" not in response.json():
            raise Exception("Unable to login.")

        self.device_token_encrypted = response.json()['devicetoken_encrypted']

        self.user_id = response.json()['userid']

        self.device_token_decrypted = self.decrypt2(response.json()['devicetoken_encrypted'], self.password)

        response = self.call("admin/login/check")

        if not response['success']:
            raise Exception("Unable to login")

        return self

    def room_list(self) -> dict:
        return self.call("api/room/list")

    def room_details(self, identifier, room_list: dict = None) -> dict | None:
        if room_list is None:
            room_list = self.room_list()

        for group in room_list['groups']:
            for room in group['rooms']:
                if room['id'] == int(identifier):
                    return room

        return None

    def system_information(self) -> dict:
        return self.call('admin/systeminformation/get')

    def set_temperature(self, room_identifier, temperature: float) -> dict:
        return self.call('api/room/settemperature', {
            "roomid": room_identifier,
            "temperature": temperature
        })

    def thermostats(self) -> list[Thermostat]:
        thermostats: list[Thermostat] = []

        try:
            response = self.room_list()
            for group in response['groups']:
                for room in group['rooms']:
                    thermostat = Thermostat(
                        identifier=room['id'],
                        module="Test",
                        name=room['name'],
                        current_temperature=room.get('actualTemperature'),
                        desired_temperature=room.get('desiredTemperature'),
                        minimum_temperature=room.get('minTemperature'),
                        maximum_temperature=room.get('minTemperature'),
                        cooling=room.get('cooling'),
                        cooling_enabled=room.get('coolingEnabled')
                    )

                    thermostats.append(thermostat)
        except Exception as exception:
            _LOGGER.exception("There is an exception: %s", exception)

        return thermostats
