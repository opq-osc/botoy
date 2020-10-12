from ..model import FriendMsg, GroupMsg


def these_msgtypes(*msgtypes):
    """仅接受该些类型消息  GroupMsg, FriendMsg
    模块collection中定义了这些消息类型
    """

    def deco(func):
        def inner(ctx):
            assert isinstance(ctx, (GroupMsg, FriendMsg))
            if ctx.MsgType in msgtypes:
                return func(ctx)
            return None

        return inner

    return deco
