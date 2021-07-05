"""See https://github.com/xiyaowong/botoy
"""
from .__version__ import check_version
from .action import Action
from .async_action import AsyncAction
from .async_client import AsyncBotoy
from .client import Botoy
from .collection import Emoticons, EventNames, MsgTypes
from .config import jconfig
from .log import logger
from .model import EventMsg, FriendMsg, GroupMsg
from .sugar import Picture, S, Text, Voice

check_version()
del check_version

__all__ = [
    "Action",
    "AsyncAction",
    "AsyncBotoy",
    "Botoy",
    "Emoticons",
    "EventNames",
    "MsgTypes",
    "jconfig",
    "logger",
    "EventMsg",
    "FriendMsg",
    "GroupMsg",
    "Picture",
    "Text",
    "Voice",
    "S",
]
