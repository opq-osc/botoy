import asyncio

from websockets.client import WebSocketClientProtocol
from websockets.client import connect as _ws_connect
from websockets.server import serve as _ws_serve

from .client import Botoy


class WebSocketClient:
    def __init__(self) -> None:
        pass

    def attach(self):
        pass


class WebSocketServer:
    pass


async def ws_connect():
    pass


async def ws_serve():
    pass
