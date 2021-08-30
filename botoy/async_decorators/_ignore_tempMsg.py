from ..model import FriendMsg


def ignore_tempMsg(func=None):
    """忽略私聊信息 FriendMsg"""
    if func is None:
        return ignore_tempMsg

    async def inner(ctx):
        assert isinstance(ctx, FriendMsg)
        if ctx.TempUin is None:
            return await func(ctx)
        return None

    return inner
