from ..collection import MsgTypes
from ..model import FriendMsg


def from_phone(func=None):
    """来自手机的消息(给自己发的) FriendMsg"""
    if func is None:
        return from_phone

    async def inner(ctx):
        assert isinstance(ctx, FriendMsg)
        if ctx.MsgType == MsgTypes.PhoneMsg:
            return await func(ctx)
        return None

    return inner
