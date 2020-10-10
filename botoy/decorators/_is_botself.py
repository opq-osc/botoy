from ..model import FriendMsg, GroupMsg


def is_botself(func=None):
    """只处理机器人自身的消息"""
    if func is None:
        return is_botself

    def inner(ctx):
        assert isinstance(ctx, (GroupMsg, FriendMsg))
        if isinstance(ctx, GroupMsg):
            userid = ctx.FromUserId
        else:
            userid = ctx.FromUin
        if userid == ctx.CurrentQQ:
            return func(ctx)
        return None

    return inner
