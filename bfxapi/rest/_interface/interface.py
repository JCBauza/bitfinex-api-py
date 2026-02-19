from .middleware import Middleware


class Interface:
    def __init__(
        self,
        host: str,
        api_key: str | None = None,
        api_secret: str | None = None,
    ):
        self._m = Middleware(host, api_key, api_secret)
