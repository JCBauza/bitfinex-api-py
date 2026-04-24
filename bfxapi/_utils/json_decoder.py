import json
import re
from typing import Any


def _to_snake_case(string: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", string).lower()


def _object_hook(data: dict[str, Any]) -> Any:
    return {_to_snake_case(key): value for key, value in data.items()}


class JSONDecoder(json.JSONDecoder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # requests uses simplejson as `complexjson` when installed; simplejson
        # passes an obsolete `encoding` kwarg that stdlib json.JSONDecoder
        # rejects on Python 3.9+ (confirmed failure on 3.12).
        kwargs.pop("encoding", None)
        super().__init__(*args, **kwargs, object_hook=_object_hook)
