from custom_components.alpha_innotec.api import BaseAPI
from . import VALID_CONFIG


def test_encode_signature():
    api = BaseAPI(
        VALID_CONFIG["controller_ip"],
        VALID_CONFIG["controller_username"],
        VALID_CONFIG["controller_password"]
    )

    assert api.encode_signature("test",
                                "test3") == b'^\x0cm\xb4\xbf`E\xf5\xbd\x83\xf9q\xc9\x80\x80\xee\xf1O<\xab\x83\x04\xca\xd6\x9d\x92\xec\x1d\xb3\xea\x1a\x8b\x85\xb7x\xb51\xea\x86%\x021\xc4G\xba\x05y\xd0\xb9\n\xf6\xb9\xc3$y\x16Hn\xeeR\x16\xb1j\x9d'


def test_decrypt2():
    api = BaseAPI(
        VALID_CONFIG["controller_ip"],
        VALID_CONFIG["controller_username"],
        VALID_CONFIG["controller_password"]
    )

    assert api.decrypt2("W9UIefCF9T7jQGmagrhsJPEldxM5iher+CSAIvbas84=",
                        "verysafepassword") == "df0f44b7163b034b91710724938af864"
