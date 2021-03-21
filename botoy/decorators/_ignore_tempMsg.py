from ..model import FriendMsg


def ignore_tempMsg(func=None):
    """忽略私聊信息 FriendMsg"""
    if func is None:
        return ignore_tempMsg

    def inner(ctx):
        assert isinstance(ctx, FriendMsg)
        if ctx.TempUin is None:
            return func(ctx)
        return None

    return inner
