import base64
import logging

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from backports.pbkdf2 import pbkdf2_hmac

_LOGGER = logging.getLogger(__name__)


class BaseAPI:

    def __init__(self, hostname: str, username: str, password: str) -> None:
        self.api_host: str = hostname
        self.username: str = username
        self.password: str = password

        self.user_id: int | None = None
        self.device_token_encrypted: str | None = None
        self.device_token_decrypted: str | None = None
        self.request_count: int = 0
        self.last_request_signature: str | None = None
        self.udid: str = "homeassistant"

    @staticmethod
    def string_to_charcodes(data: str) -> str:
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

    @staticmethod
    def _prepare_request_body_for_hash(urlencoded_string: str) -> str:
        """Replace dots for comma in case of temperature being passed"""
        urlencoded_string = urlencoded_string.replace('%2C', ',').replace('%5B', '[').replace('%5D', ']')
        # if(urlencodedString.find("temperature") != -1):
        #    urlencodedString = urlencodedString.replace('.', ',')
        return urlencoded_string

    @staticmethod
    def decrypt2(encrypted_data: str, key: str):
        static_iv = 'D3GC5NQEFH13is04KD2tOg=='
        crypt_key = SHA256.new()
        crypt_key.update(bytes(key, 'utf-8'))
        crypt_key = crypt_key.digest()
        cipher = AES.new(crypt_key, AES.MODE_CBC, base64.b64decode(static_iv))

        return cipher.decrypt(base64.b64decode(encrypted_data)).decode('ascii').strip('\x10')
