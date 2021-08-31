from ..model import FriendMsg, GroupMsg
from ..parser import friend as fp
from ..parser import group as gp


def equal_content(string: str):
    """发送的内容与指定字符串相等时 GroupMsg, FriendMsg"""

    def deco(func):
        async def inner(ctx):
            assert isinstance(ctx, (GroupMsg, FriendMsg))
            if isinstance(ctx, GroupMsg):
                pic_data = gp.pic(ctx)
            else:
                pic_data = fp.pic(ctx)
            if pic_data is not None:
                content = pic_data.Content
            else:
                content = ctx.Content
            if content == string:
                return await func(ctx)
            return None

        return inner

    return deco
