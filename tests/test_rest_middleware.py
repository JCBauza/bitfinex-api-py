import hashlib
import hmac
from unittest.mock import MagicMock, patch

import pytest

from bfxapi.exceptions import InvalidCredentialError
from bfxapi.rest._interface.middleware import Middleware, _Error
from bfxapi.rest.exceptions import GenericError, RequestParameterError


class TestMiddlewareGet:
    @patch("bfxapi.rest._interface.middleware.requests.get")
    def test_get_public_no_auth(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [1]
        mock_get.return_value = mock_response

        m = Middleware("https://api.example.com")
        result = m.get("v2/platform/status")

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert (
            call_kwargs.kwargs["url"]
            == "https://api.example.com/v2/platform/status"
        )
        assert "bfx-apikey" not in call_kwargs.kwargs["headers"]
        assert result == [1]

    @patch("bfxapi.rest._interface.middleware.requests.get")
    def test_get_with_params(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        m = Middleware("https://api.example.com")
        m.get("v2/tickers", params={"symbols": "tBTCUSD"})

        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"] == {"symbols": "tBTCUSD"}

    @patch("bfxapi.rest._interface.middleware.requests.get")
    def test_get_with_auth_headers(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        m = Middleware(
            "https://api.example.com", api_key="key", api_secret="secret"
        )
        m.get("v2/auth/r/wallets")

        call_kwargs = mock_get.call_args
        headers = call_kwargs.kwargs["headers"]
        assert "bfx-apikey" in headers
        assert "bfx-nonce" in headers
        assert "bfx-signature" in headers
        assert headers["bfx-apikey"] == "key"

    @patch("bfxapi.rest._interface.middleware.requests.get")
    def test_get_timeout(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        m = Middleware("https://api.example.com")
        m.get("v2/platform/status")

        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["timeout"] == 30


class TestMiddlewarePost:
    @patch("bfxapi.rest._interface.middleware.requests.post")
    def test_post_with_body(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = [1]
        mock_post.return_value = mock_response

        m = Middleware(
            "https://api.example.com", api_key="key", api_secret="secret"
        )
        result = m.post("v2/auth/w/order/submit", body={"type": "LIMIT"})

        call_kwargs = mock_post.call_args
        assert (
            call_kwargs.kwargs["url"]
            == "https://api.example.com/v2/auth/w/order/submit"
        )
        assert "Content-Type" in call_kwargs.kwargs["headers"]
        assert (
            call_kwargs.kwargs["headers"]["Content-Type"] == "application/json"
        )
        assert result == [1]

    @patch("bfxapi.rest._interface.middleware.requests.post")
    def test_post_no_body(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_post.return_value = mock_response

        m = Middleware(
            "https://api.example.com", api_key="key", api_secret="secret"
        )
        m.post("v2/auth/r/orders")

        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["data"] is None


class TestMiddlewareErrorHandling:
    @patch("bfxapi.rest._interface.middleware.requests.get")
    def test_request_parameter_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = ["error", 10020, "Invalid parameters"]
        mock_get.return_value = mock_response

        m = Middleware("https://api.example.com")
        with pytest.raises(RequestParameterError, match="parameter error"):
            m.get("v2/invalid")

    @patch("bfxapi.rest._interface.middleware.requests.get")
    def test_auth_fail_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = ["error", 10100, "Auth failed"]
        mock_get.return_value = mock_response

        m = Middleware("https://api.example.com")
        with pytest.raises(InvalidCredentialError, match="API-KEY"):
            m.get("v2/auth/r/wallets")

    @patch("bfxapi.rest._interface.middleware.requests.get")
    def test_generic_error_unk(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = ["error", 10000, "Unknown error"]
        mock_get.return_value = mock_response

        m = Middleware("https://api.example.com")
        with pytest.raises(GenericError, match="generic error"):
            m.get("v2/something")

    @patch("bfxapi.rest._interface.middleware.requests.get")
    def test_generic_error_generic(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = ["error", 10001, "Generic error"]
        mock_get.return_value = mock_response

        m = Middleware("https://api.example.com")
        with pytest.raises(GenericError):
            m.get("v2/something")

    @patch("bfxapi.rest._interface.middleware.requests.get")
    def test_generic_error_falsy_code(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = ["error", 0, "Falsy error"]
        mock_get.return_value = mock_response

        m = Middleware("https://api.example.com")
        with pytest.raises(GenericError):
            m.get("v2/something")

    @patch("bfxapi.rest._interface.middleware.requests.get")
    def test_unexpected_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = ["error", 99999, "Weird error"]
        mock_get.return_value = mock_response

        m = Middleware("https://api.example.com")
        with pytest.raises(RuntimeError, match="unexpected error"):
            m.get("v2/something")

    @patch("bfxapi.rest._interface.middleware.requests.get")
    def test_non_error_response_passes_through(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [1, 2, 3]
        mock_get.return_value = mock_response

        m = Middleware("https://api.example.com")
        result = m.get("v2/something")
        assert result == [1, 2, 3]


class TestMiddlewareAuthentication:
    def test_signature_algorithm(self):
        m = Middleware(
            "https://api.example.com",
            api_key="testkey",
            api_secret="testsecret",
        )

        # Access private method for testing
        headers = m._Middleware__get_authentication_headers("v2/auth/r/wallets")

        nonce = headers["bfx-nonce"]
        message = f"/api/v2/v2/auth/r/wallets{nonce}"
        expected_sig = hmac.new(
            key=b"testsecret",
            msg=message.encode("utf8"),
            digestmod=hashlib.sha384,
        ).hexdigest()

        assert headers["bfx-signature"] == expected_sig
        assert headers["bfx-apikey"] == "testkey"

    def test_signature_with_data(self):
        m = Middleware(
            "https://api.example.com",
            api_key="testkey",
            api_secret="testsecret",
        )

        data = '{"type": "LIMIT"}'
        headers = m._Middleware__get_authentication_headers(
            "v2/auth/w/order", data
        )

        nonce = headers["bfx-nonce"]
        message = f"/api/v2/v2/auth/w/order{nonce}{data}"
        expected_sig = hmac.new(
            key=b"testsecret",
            msg=message.encode("utf8"),
            digestmod=hashlib.sha384,
        ).hexdigest()

        assert headers["bfx-signature"] == expected_sig


class TestErrorEnum:
    def test_error_values(self):
        assert _Error.ERR_UNK == 10000
        assert _Error.ERR_GENERIC == 10001
        assert _Error.ERR_PARAMS == 10020
        assert _Error.ERR_AUTH_FAIL == 10100
