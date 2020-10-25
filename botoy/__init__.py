"""See https://github.com/xiyaowong/botoy
"""
try:
    import ujson as json
except ImportError:
    import json

from . import decorators, refine
from .action import Action
from .async_action import AsyncAction
from .async_client import AsyncBotoy
from .client import Botoy
from .model import EventMsg, FriendMsg, GroupMsg

__all__ = [
    'refine',
    'decorators',
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

from .__version__ import check_version as __check_version

__check_version()
