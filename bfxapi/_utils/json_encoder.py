import json
from decimal import Decimal
from typing import Any

_ExtJSON = (
    dict[str, "_ExtJSON"]
    | list["_ExtJSON"]
    | bool
    | int
    | float
    | str
    | Decimal
    | None
)

_StrictJSON = dict[str, "_StrictJSON"] | list["_StrictJSON"] | int | str | None


def _clear(dictionary: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in dictionary.items() if value is not None
    }


def _adapter(data: _ExtJSON) -> _StrictJSON:
    if isinstance(data, bool):
        return int(data)
    if isinstance(data, float):
        return format(Decimal(repr(data)), "f")
    if isinstance(data, Decimal):
        return format(data, "f")

    if isinstance(data, list):
        return [_adapter(sub_data) for sub_data in data]
    if isinstance(data, dict):
        return _clear({key: _adapter(value) for key, value in data.items()})

    return data


class JSONEncoder(json.JSONEncoder):
    def encode(self, o: _ExtJSON) -> str:
        return super().encode(_adapter(o))
