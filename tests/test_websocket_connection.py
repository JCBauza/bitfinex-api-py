import hashlib
import hmac
import json
from unittest.mock import MagicMock, PropertyMock

import pytest

from bfxapi.websocket._connection import Connection
from bfxapi.websocket.exceptions import (
    ActionRequiresAuthentication,
    ConnectionNotOpen,
)


class ConcreteConnection(Connection):
    """Concrete subclass for testing the abstract Connection."""

    async def start(self) -> None:
        pass


class TestConnectionProperties:
    def test_open_initially_false(self):
        conn = ConcreteConnection("wss://example.com")
        assert conn.open is False

    def test_authentication_initially_false(self):
        conn = ConcreteConnection("wss://example.com")
        assert conn.authentication is False

    def test_set_authentication(self):
        conn = ConcreteConnection("wss://example.com")
        conn._authentication = True
        assert conn.authentication is True


class TestRequireWebsocketConnection:
    @pytest.mark.asyncio
    async def test_raises_when_not_connected(self):
        conn = ConcreteConnection("wss://example.com")

        @Connection._require_websocket_connection
        async def some_action(self):
            return "success"

        with pytest.raises(ConnectionNotOpen, match="No open connection"):
            await some_action(conn)

    @pytest.mark.asyncio
    async def test_passes_when_connected(self):
        conn = ConcreteConnection("wss://example.com")
        mock_ws = MagicMock()
        mock_state = MagicMock()
        mock_state.name = "OPEN"
        type(mock_ws).state = PropertyMock(return_value=mock_state)
        conn._websocket = mock_ws

        @Connection._require_websocket_connection
        async def some_action(self):
            return "success"

        result = await some_action(conn)
        assert result == "success"


class TestRequireWebsocketAuthentication:
    @pytest.mark.asyncio
    async def test_raises_when_not_authenticated(self):
        conn = ConcreteConnection("wss://example.com")

        @Connection._require_websocket_authentication
        async def auth_action(self):
            return "success"

        with pytest.raises(
            ActionRequiresAuthentication,
            match="authenticate using your API_KEY",
        ):
            await auth_action(conn)

    @pytest.mark.asyncio
    async def test_raises_when_authenticated_but_not_connected(self):
        conn = ConcreteConnection("wss://example.com")
        conn._authentication = True

        @Connection._require_websocket_authentication
        async def auth_action(self):
            return "success"

        with pytest.raises(ConnectionNotOpen):
            await auth_action(conn)

    @pytest.mark.asyncio
    async def test_passes_when_authenticated_and_connected(self):
        conn = ConcreteConnection("wss://example.com")
        conn._authentication = True
        mock_ws = MagicMock()
        mock_state = MagicMock()
        mock_state.name = "OPEN"
        type(mock_ws).state = PropertyMock(return_value=mock_state)
        conn._websocket = mock_ws

        @Connection._require_websocket_authentication
        async def auth_action(self):
            return "success"

        result = await auth_action(conn)
        assert result == "success"


class TestGetAuthenticationMessage:
    def test_message_structure(self):
        msg = json.loads(
            Connection._get_authentication_message(
                api_key="test_key", api_secret="test_secret"
            )
        )
        assert msg["event"] == "auth"
        assert msg["apiKey"] == "test_key"
        assert "authNonce" in msg
        assert "authPayload" in msg
        assert "authSig" in msg

    def test_payload_format(self):
        msg = json.loads(
            Connection._get_authentication_message(
                api_key="key", api_secret="secret"
            )
        )
        assert msg["authPayload"] == f"AUTH{msg['authNonce']}"

    def test_signature_correctness(self):
        api_secret = "my_secret"
        msg = json.loads(
            Connection._get_authentication_message(
                api_key="key", api_secret=api_secret
            )
        )
        expected_sig = hmac.new(
            key=api_secret.encode("utf8"),
            msg=msg["authPayload"].encode("utf8"),
            digestmod=hashlib.sha384,
        ).hexdigest()
        assert msg["authSig"] == expected_sig

    def test_filters_included(self):
        msg = json.loads(
            Connection._get_authentication_message(
                api_key="key",
                api_secret="secret",
                filters=["trading", "funding"],
            )
        )
        assert msg["filter"] == ["trading", "funding"]

    def test_filters_none_by_default(self):
        msg = json.loads(
            Connection._get_authentication_message(
                api_key="key", api_secret="secret"
            )
        )
        assert msg["filter"] is None

    def test_nonce_is_integer(self):
        msg = json.loads(
            Connection._get_authentication_message(
                api_key="key", api_secret="secret"
            )
        )
        assert isinstance(msg["authNonce"], int)
        assert msg["authNonce"] > 0
