import base64
import logging
import urllib
from urllib.parse import unquote

import requests
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from backports.pbkdf2 import pbkdf2_hmac

_LOGGER = logging.getLogger(__name__)


class ControllerApi:

    def __init__(self, hostname, username, password) -> None:
        self.username = username
        self.password = password
        self.api_host = hostname

        self.user_id = None
        self.device_token_encrypted = None
        self.device_token_decrypted = None
        self.request_count = 0
        self.last_request_signature = None
        self.udid = "homeassistant"

    @staticmethod
    def string_to_charcodes(data: str):
        a = ""
        if len(data) > 0:
            for i in range(len(data)):
                t = str(ord(data[i]))
                while len(t) < 3:
                    t = "0" + t
                a += t

        return a

    def encode_signature(self, value: str, salt: str) -> str:
        value = self.string_to_charcodes(value)
        salt = self.string_to_charcodes(salt)

        original = pbkdf2_hmac("sha512", value.encode(), salt.encode(), 1)

        return original

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

    @staticmethod
    def _prepare_request_body_for_hash(urlencoded_string):
        urlencoded_string = urlencoded_string.replace('%2C', ',').replace('%5B', '[').replace('%5D', ']')
        """Replace dots for comma in case of temperature being passed"""
        # if(urlencodedString.find("temperature") != -1):
        #    urlencodedString = urlencodedString.replace('.', ',')
        return urlencoded_string

    @staticmethod
    def decrypt2(encrypted_data, key):
        static_iv = 'D3GC5NQEFH13is04KD2tOg=='
        crypt_key = SHA256.new()
        crypt_key.update(bytes(key, 'utf-8'))
        crypt_key = crypt_key.digest()
        cipher = AES.new(crypt_key, AES.MODE_CBC, base64.b64decode(static_iv))

        return cipher.decrypt(base64.b64decode(encrypted_data)).decode('ascii').strip('\x10')

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
            json_response = response.json()
        except Exception as exception:
            _LOGGER.exception("Unable to fetch data from API: %s", exception)

        _LOGGER.debug("Response: %s", json_response)

        if not json_response['success']:
            raise Exception('Failed to get data')
        else:
            _LOGGER.debug('Successfully fetched data from API')

        return json_response

    def room_list(self):
        return self.call("api/room/list")

    def room_details(self, identifier):
        room_list = self.room_list()
        for group in room_list['groups']:
            for room in group['rooms']:
                if room['id'] == identifier:
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


class Thermostat:
    def __init__(self, identifier: str, name: str, module: str = None, current_temperature: float = None,
                 minimum_temperature: float = None, maximum_temperature: float = None,
                 desired_temperature: float = None, battery_percentage: int = None,
                 cooling: bool = None,
                 cooling_enabled: bool = False
                 ):
        self.identifier = identifier
        self.module = module
        self.name = name
        self.current_temperature = current_temperature
        self.minimum_temperature = minimum_temperature
        self.maximum_temperature = maximum_temperature
        self.battery_percentage = battery_percentage
        self.desired_temperature = desired_temperature
        self.cooling = cooling
        self.cooling_enabled = cooling_enabled
