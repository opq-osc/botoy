from ..model import FriendMsg


def ensure_tempMsg(func=None):
    """只接收私聊信息 FriendMsg"""
    if func is None:
        return ensure_tempMsg

    def inner(ctx):
        assert isinstance(ctx, FriendMsg)
        if ctx.TempUin is not None:
            return func(ctx)
        return None

    return inner
