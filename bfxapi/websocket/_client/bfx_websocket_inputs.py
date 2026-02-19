from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import Any

_Handler = Callable[[str, Any], Awaitable[None]]


class BfxWebSocketInputs:
    def __init__(self, handle_websocket_input: _Handler) -> None:
        self.__handle_websocket_input = handle_websocket_input

    async def submit_order(
        self,
        type: str,
        symbol: str,
        amount: str | float | Decimal,
        price: str | float | Decimal,
        *,
        lev: int | None = None,
        price_trailing: str | float | Decimal | None = None,
        price_aux_limit: str | float | Decimal | None = None,
        price_oco_stop: str | float | Decimal | None = None,
        gid: int | None = None,
        cid: int | None = None,
        flags: int | None = None,
        tif: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        await self.__handle_websocket_input(
            "on",
            {
                "type": type,
                "symbol": symbol,
                "amount": amount,
                "price": price,
                "lev": lev,
                "price_trailing": price_trailing,
                "price_aux_limit": price_aux_limit,
                "price_oco_stop": price_oco_stop,
                "gid": gid,
                "cid": cid,
                "flags": flags,
                "tif": tif,
                "meta": meta,
            },
        )

    async def update_order(
        self,
        id: int,
        *,
        amount: str | float | Decimal | None = None,
        price: str | float | Decimal | None = None,
        cid: int | None = None,
        cid_date: str | None = None,
        gid: int | None = None,
        flags: int | None = None,
        lev: int | None = None,
        delta: str | float | Decimal | None = None,
        price_aux_limit: str | float | Decimal | None = None,
        price_trailing: str | float | Decimal | None = None,
        tif: str | None = None,
    ) -> None:
        await self.__handle_websocket_input(
            "ou",
            {
                "id": id,
                "amount": amount,
                "price": price,
                "cid": cid,
                "cid_date": cid_date,
                "gid": gid,
                "flags": flags,
                "lev": lev,
                "delta": delta,
                "price_aux_limit": price_aux_limit,
                "price_trailing": price_trailing,
                "tif": tif,
            },
        )

    async def cancel_order(
        self,
        *,
        id: int | None = None,
        cid: int | None = None,
        cid_date: str | None = None,
    ) -> None:
        await self.__handle_websocket_input(
            "oc", {"id": id, "cid": cid, "cid_date": cid_date}
        )

    async def cancel_order_multi(
        self,
        *,
        id: list[int] | None = None,
        cid: list[tuple[int, str]] | None = None,
        gid: list[int] | None = None,
        all: bool | None = None,
    ) -> None:
        await self.__handle_websocket_input(
            "oc_multi", {"id": id, "cid": cid, "gid": gid, "all": all}
        )

    async def submit_funding_offer(
        self,
        type: str,
        symbol: str,
        amount: str | float | Decimal,
        rate: str | float | Decimal,
        period: int,
        *,
        flags: int | None = None,
    ) -> None:
        await self.__handle_websocket_input(
            "fon",
            {
                "type": type,
                "symbol": symbol,
                "amount": amount,
                "rate": rate,
                "period": period,
                "flags": flags,
            },
        )

    async def cancel_funding_offer(self, id: int) -> None:
        await self.__handle_websocket_input("foc", {"id": id})

    async def calc(self, *args: str) -> None:
        await self.__handle_websocket_input(
            "calc", list(map(lambda arg: [arg], args))
        )
