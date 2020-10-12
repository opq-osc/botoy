from ..model import FriendMsg, GroupMsg


def from_these_users(*users):
    """仅接受来自这些用户的消息 GroupMsg, FriendMsg"""

    def deco(func):
        def inner(ctx):
            nonlocal users
            assert isinstance(ctx, (GroupMsg, FriendMsg))
            if isinstance(ctx, GroupMsg):
                from_user = ctx.FromUserId
            elif isinstance(ctx, FriendMsg):
                from_user = ctx.FromUin
            if from_user in users:
                return func(ctx)
            return None

        return inner

    return deco
