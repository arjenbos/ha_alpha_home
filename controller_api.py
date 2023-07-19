from .api import BaseAPI
import requests
import logging
import base64
import urllib
from urllib.parse import unquote

from .structs.Thermostat import Thermostat

_LOGGER = logging.getLogger(__name__)


class ControllerAPI(BaseAPI):

    def call(self, endpoint: str, data: dict = {}):
        _LOGGER.debug("Requesting: %s", endpoint)
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

            _LOGGER.debug("Encoded body: %s", urlencoded_body)

            response = requests.post("http://{hostname}/{endpoint}".format(hostname=self.api_host, endpoint=endpoint),
                                     data=urlencoded_body,
                                     headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
                                     )

            self.request_count = self.request_count + 1

            _LOGGER.debug("Response: %s", response)
            json_response = response.json()
        except Exception as exception:
            _LOGGER.exception("Unable to fetch data from API: %s", exception)

        _LOGGER.debug("JSON Response: %s", json_response)

        if not json_response['success']:
            raise Exception('Failed to get data')
        else:
            _LOGGER.debug('Successfully fetched data from API')

        return json_response

    def login(self):
        response = requests.post("http://" + self.api_host + "/api/user/token/challenge", data={
            "udid": self.udid
        })

        device_token = response.json()['devicetoken']

        response = requests.post("http://" + self.api_host + "/api/user/token/response", data={
            "login": self.username,
            "token": device_token,
            "udid": self.udid,
            "hashed": base64.b64encode(self.encode_signature(self.password, device_token)).decode()
        })

        self.device_token_encrypted = response.json()['devicetoken_encrypted']
        self.user_id = response.json()['userid']

        self.device_token_decrypted = self.decrypt2(response.json()['devicetoken_encrypted'], self.password)

        response = self.call("admin/login/check")

        if not response['success']:
            raise Exception("Unable to login")

        return self

    def room_list(self):
        return self.call("api/room/list")

    def room_details(self, identifier):
        room_list = self.room_list()
        for group in room_list['groups']:
            for room in group['rooms']:
                if room['id'] == int(identifier):
                    return room

        return None

    def system_information(self):
        return self.call('admin/systeminformation/get')

    def set_temperature(self, room_identifier, temperature: float):
        return self.call('api/room/settemperature', {
            "roomid": room_identifier,
            "temperature": temperature
        })

    def thermostats(self):
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