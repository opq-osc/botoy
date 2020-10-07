"""See https://github.com/xiyaowong/botoy
"""
try:
    import ujson as json
except ImportError:
    import json

# from botoy import decorators, macro, middlewares, refine, sugar, util
from botoy.action import Action
from botoy.client import Botoy
from botoy.model import EventMsg, FriendMsg, GroupMsg
