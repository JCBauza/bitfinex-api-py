from bfxapi.rest._interfaces import RestAuthEndpoints, RestPublicEndpoints


class BfxRestInterface:
    def __init__(
        self,
        host: str,
        api_key: str | None = None,
        api_secret: str | None = None,
    ):
        self.auth = RestAuthEndpoints(
            host=host, api_key=api_key, api_secret=api_secret
        )

        self.public = RestPublicEndpoints(host=host)
