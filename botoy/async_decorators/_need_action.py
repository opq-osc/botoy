from ..async_action import AsyncAction


def need_action(func=None):
    """自动创建action并作为接收函数第2个参数传入
    你需要修改接收函数, 并且该装饰器只能放在最后（下）面!
    """
    if func is None:
        return need_action

    async def inner(ctx):
        action = AsyncAction(
            ctx.CurrentQQ,
            host=getattr(ctx, "_host", None),
            port=getattr(ctx, "_port", None),
        )
        return await func(ctx, action)

    return inner
