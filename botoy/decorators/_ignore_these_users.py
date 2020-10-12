from ..model import FriendMsg, GroupMsg


def ignore_these_users(*users):
    """忽略这些人的消息 GroupMsg, FriendMsg"""

    def deco(func):
        def inner(ctx):
            nonlocal users
            assert isinstance(ctx, (GroupMsg, FriendMsg))
            if isinstance(ctx, GroupMsg):
                from_user = ctx.FromUserId
            elif isinstance(ctx, FriendMsg):
                from_user = ctx.FromUin
            if from_user not in users:
                return func(ctx)
            return None

        return inner

    return deco
