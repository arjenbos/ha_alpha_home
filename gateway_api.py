from .api import BaseAPI
import requests
import logging
import base64
import urllib
from urllib.parse import unquote

_LOGGER = logging.getLogger(__name__)


class GatewayAPI(BaseAPI):
    username = "gateway"

    def __init__(self, hostname, password) -> None:
        super().__init__(hostname, self.username, password)
        self.password = password
        self.api_host = hostname

        self.request_count = 0
        self.last_request_signature = None
        self.udid = "homeassistant"


    def call(self, endpoint: str, data: dict = {}):
        _LOGGER.debug("Requesting: %s", endpoint)
        json_response = None

        try:
            data['userlogin'] = self.username
            data['udid'] = self.udid
            data['reqcount'] = self.request_count

            post_data_sorted = sorted(data.items(), key=lambda val: val[0])

            urlencoded_body = urllib.parse.urlencode(post_data_sorted, encoding='utf-8')
            urlencoded_body_prepared_for_hash = self._prepare_request_body_for_hash(urlencoded_body)
            urlencoded_body_prepared_for_hash = urlencoded_body_prepared_for_hash.replace('&', '|')
            urlencoded_body_prepared_for_hash = urlencoded_body_prepared_for_hash + "|"

            request_signature = base64.b64encode(
                self.encode_signature(urlencoded_body_prepared_for_hash, self.password)).decode()

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
        response = self.call("admin/login/check")

        _LOGGER.debug("Login check response: %s", response)

        if not response['success']:
            raise Exception("Unable to login")

        return self

    def all_modules(self):
        response = self.call("api/gateway/allmodules")
        _LOGGER.debug(response)

        return response['modules']['rooms']

    def db_modules(self):
        return self.call("api/gateway/dbmodules")

    def get_module_details(self, module_id):
        response = self.db_modules()
        if module_id in response['modules']:
            return response['modules'][module_id]

        return None
