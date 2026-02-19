import json
from decimal import Decimal

from bfxapi._utils.json_encoder import JSONEncoder, _adapter, _clear


class TestClear:
    def test_removes_none_values(self):
        assert _clear({"a": 1, "b": None, "c": 3}) == {"a": 1, "c": 3}

    def test_keeps_falsy_non_none_values(self):
        assert _clear({"a": 0, "b": "", "c": False, "d": []}) == {
            "a": 0,
            "b": "",
            "c": False,
            "d": [],
        }

    def test_empty_dict(self):
        assert _clear({}) == {}

    def test_all_none(self):
        assert _clear({"a": None, "b": None}) == {}


class TestAdapter:
    def test_bool_to_int(self):
        assert _adapter(True) == 1
        assert _adapter(False) == 0

    def test_float_precision(self):
        result = _adapter(0.1)
        assert result == "0.1"
        assert isinstance(result, str)

    def test_float_large_number(self):
        result = _adapter(123456.789)
        assert result == "123456.789"

    def test_decimal(self):
        result = _adapter(Decimal("3.14159"))
        assert result == "3.14159"

    def test_int_passthrough(self):
        assert _adapter(42) == 42

    def test_str_passthrough(self):
        assert _adapter("hello") == "hello"

    def test_none_passthrough(self):
        assert _adapter(None) is None

    def test_list_recursive(self):
        result = _adapter([True, 0.5, "text", None])
        assert result == [1, "0.5", "text", None]

    def test_dict_recursive_removes_none(self):
        result = _adapter({"a": True, "b": 0.5, "c": None})
        assert result == {"a": 1, "b": "0.5"}

    def test_nested_structure(self):
        result = _adapter({"items": [True, {"price": 0.1, "unused": None}]})
        assert result == {"items": [1, {"price": "0.1"}]}


class TestJSONEncoder:
    def test_encode_bool(self):
        assert json.dumps(True, cls=JSONEncoder) == "1"
        assert json.dumps(False, cls=JSONEncoder) == "0"

    def test_encode_float(self):
        assert json.dumps(0.1, cls=JSONEncoder) == '"0.1"'

    def test_encode_decimal(self):
        assert json.dumps(Decimal("99.99"), cls=JSONEncoder) == '"99.99"'

    def test_encode_dict_filters_none(self):
        result = json.loads(json.dumps({"a": 1, "b": None}, cls=JSONEncoder))
        assert result == {"a": 1}

    def test_encode_complex_order_payload(self):
        payload = {
            "type": "EXCHANGE LIMIT",
            "symbol": "tBTCUSD",
            "amount": 0.001,
            "price": 50000.50,
            "hidden": False,
        }
        result = json.loads(json.dumps(payload, cls=JSONEncoder))
        assert result == {
            "type": "EXCHANGE LIMIT",
            "symbol": "tBTCUSD",
            "amount": "0.001",
            "price": "50000.5",
            "hidden": 0,
        }
