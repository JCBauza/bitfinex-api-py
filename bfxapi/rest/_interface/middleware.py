import hashlib
import hmac
import json
from datetime import datetime
from enum import IntEnum
from typing import TYPE_CHECKING, Any, NoReturn

import requests

from bfxapi._utils.json_decoder import JSONDecoder
from bfxapi._utils.json_encoder import JSONEncoder
from bfxapi.exceptions import InvalidCredentialError
from bfxapi.rest.exceptions import GenericError, RequestParameterError

if TYPE_CHECKING:
    from requests.sessions import _Params


class _Error(IntEnum):
    ERR_UNK = 10000
    ERR_GENERIC = 10001
    ERR_PARAMS = 10020
    ERR_AUTH_FAIL = 10100


class Middleware:
    __TIMEOUT = 30

    def __init__(
        self,
        host: str,
        api_key: str | None = None,
        api_secret: str | None = None,
    ):
        self.__host = host

        self.__api_key = api_key

        self.__api_secret = api_secret

    def get(self, endpoint: str, params: "_Params | None" = None) -> Any:
        headers = {"Accept": "application/json"}

        if self.__api_key and self.__api_secret:
            headers = {**headers, **self.__get_authentication_headers(endpoint)}

        request = requests.get(
            url=f"{self.__host}/{endpoint}",
            params=params,
            headers=headers,
            timeout=Middleware.__TIMEOUT,
        )

        data = request.json(cls=JSONDecoder)

        if isinstance(data, list) and len(data) > 0 and data[0] == "error":
            self.__handle_error(data)

        return data

    def post(
        self,
        endpoint: str,
        body: Any | None = None,
        params: "_Params | None" = None,
    ) -> Any:
        _body = body and json.dumps(body, cls=JSONEncoder) or None

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.__api_key and self.__api_secret:
            headers = {
                **headers,
                **self.__get_authentication_headers(endpoint, _body),
            }

        request = requests.post(
            url=f"{self.__host}/{endpoint}",
            data=_body,
            params=params,
            headers=headers,
            timeout=Middleware.__TIMEOUT,
        )

        data = request.json(cls=JSONDecoder)

        if isinstance(data, list) and len(data) > 0 and data[0] == "error":
            self.__handle_error(data)

        return data

    def __handle_error(self, error: list[Any]) -> NoReturn:
        if error[1] == _Error.ERR_PARAMS:
            raise RequestParameterError(
                "The request was rejected with the following parameter "
                f"error: <{error[2]}>."
            )

        if error[1] == _Error.ERR_AUTH_FAIL:
            raise InvalidCredentialError(
                "Can't authenticate with given API-KEY and API-SECRET."
            )

        if (
            not error[1]
            or error[1] == _Error.ERR_UNK
            or error[1] == _Error.ERR_GENERIC
        ):
            raise GenericError(
                "The request was rejected with the following generic "
                f"error: <{error[2]}>."
            )

        raise RuntimeError(
            f"The request was rejected with an unexpected error: <{error}>."
        )

    def __get_authentication_headers(
        self, endpoint: str, data: str | None = None
    ):
        assert self.__api_key and self.__api_secret

        nonce = str(round(datetime.now().timestamp() * 1_000_000))

        if not data:
            message = f"/api/v2/{endpoint}{nonce}"
        else:
            message = f"/api/v2/{endpoint}{nonce}{data}"

        signature = hmac.new(
            key=self.__api_secret.encode("utf8"),
            msg=message.encode("utf8"),
            digestmod=hashlib.sha384,
        )

        return {
            "bfx-nonce": nonce,
            "bfx-signature": signature.hexdigest(),
            "bfx-apikey": self.__api_key,
        }
