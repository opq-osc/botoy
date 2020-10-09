"""See https://github.com/xiyaowong/botoy
"""
try:
    import ujson as json
except ImportError:
    import json

from botoy import collection, decorators, middlewares, refine, sugar
from botoy.action import Action
from botoy.async_action import AsyncAction
from botoy.async_client import AsyncBotoy
from botoy.client import Botoy
from botoy.model import EventMsg, FriendMsg, GroupMsg

__all__ = [
    'refine',
    'decorators',
    'middlewares',
    'sugar',
    'collection',
    'Action',
    'AsyncAction',
    'Botoy',
    'AsyncBotoy',
    'EventMsg',
    'GroupMsg',
    'FriendMsg',
]
