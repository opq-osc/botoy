"""See https://github.com/xiyaowong/botoy
"""
try:
    import ujson as json
except ImportError:
    import json

from .__version__ import check_version
from .action import Action
from .async_action import AsyncAction
from .async_client import AsyncBotoy
from .client import Botoy
from .collection import Emoticons, EventNames, MsgTypes
from .config import jconfig
from .log import logger
from .model import EventMsg, FriendMsg, GroupMsg
from .sugar import Picture, Text, Voice

check_version()
del check_version
