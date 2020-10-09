from botoy import FriendMsg, GroupMsg


def from_these_groups(*groups):
    """只接受这些群组的消息"""

    def deco(func):
        def inner(ctx):
            nonlocal groups
            assert isinstance(ctx, (GroupMsg, FriendMsg))
            from_group = ctx.FromGroupId
            if from_group in groups:
                return func(ctx)
            return None

        return inner

    return deco
