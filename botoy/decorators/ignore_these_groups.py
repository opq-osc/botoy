from botoy import FriendMsg, GroupMsg


def ignore_these_groups(*groups):
    """不接受这些群组的消息"""

    def deco(func):
        def inner(ctx):
            nonlocal groups
            assert isinstance(ctx, (GroupMsg, FriendMsg))
            from_group = ctx.FromGroupId
            if from_group not in groups:
                return func(ctx)
            return None

        return inner

    return deco
