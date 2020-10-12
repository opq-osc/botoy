from ..model import GroupMsg


def ignore_these_groups(*groups):
    """不接受这些群组的消息 GroupMsg"""

    def deco(func):
        def inner(ctx):
            nonlocal groups
            assert isinstance(ctx, GroupMsg)
            from_group = ctx.FromGroupId
            if from_group not in groups:
                return func(ctx)
            return None

        return inner

    return deco
