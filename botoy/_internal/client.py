import typing as t

from websockets.client import connect as ws_connect


class Botoy:
    def __init__(self):
        self._use_plugins = False

    def enable_plugins(self):
        self._use_plugins = True
