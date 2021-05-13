from contextvars import ContextVar
from typing import Union

from ..model import FriendMsg, GroupMsg
from .base import Session


def bind_contextvar(contextvar):
    class ContextVarBind:
        __slots__ = ()

        def __getattr__(self, name):
            return getattr(contextvar.get(), name)

        def __setattr__(self, name, value):
            setattr(contextvar.get(), name, value)

        def __delattr__(self, name):
            delattr(contextvar.get(), name)

        def __getitem__(self, index):
            return contextvar.get()[index]

        def __setitem__(self, index, value):
            contextvar.get()[index] = value

        def __delitem__(self, index):
            del contextvar.get()[index]

    return ContextVarBind()


_ctx: ContextVar[Union[FriendMsg, GroupMsg]] = ContextVar("ctx")
_session: ContextVar[Session] = ContextVar("session")

ctx: Union[FriendMsg, GroupMsg] = bind_contextvar(_ctx)
session: Session = bind_contextvar(_session)
