from contextvars import ContextVar
from typing import Union

from ..model import FriendMsg, GroupMsg
from .base import Session


class ContextVarProxy:
    def __init__(self, var):
        self.var = var

    def __getattr__(self, attr):
        return getattr(self.var.get(), attr)


_ctx = ContextVar("ctx")
_session = ContextVar("session")

ctx: Union[FriendMsg, GroupMsg] = ContextVarProxy(_ctx)
session: Session = ContextVarProxy(_session)
