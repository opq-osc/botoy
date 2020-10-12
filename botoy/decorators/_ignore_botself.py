from ..model import FriendMsg, GroupMsg


def ignore_botself(func=None):
    """忽略机器人自身的消息 GroupMsg, FriendMsg"""
    if func is None:
        return ignore_botself

    def inner(ctx):
        assert isinstance(ctx, (GroupMsg, FriendMsg))
        if isinstance(ctx, GroupMsg):
            userid = ctx.FromUserId
        else:
            userid = ctx.FromUin
        if userid != ctx.CurrentQQ:
            return func(ctx)
        return None

    return inner
