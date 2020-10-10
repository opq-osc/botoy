from ..model import FriendMsg, GroupMsg
from ..refine import refine_pic_friend_msg, refine_pic_group_msg


def equal_content(string: str):
    """发送的内容与指定字符串相等时 GroupMsg, FriendMsg"""

    def deco(func):
        def inner(ctx):
            assert isinstance(ctx, (GroupMsg, FriendMsg))
            if isinstance(ctx, GroupMsg):
                pic_ctx = refine_pic_group_msg(ctx)
            else:
                pic_ctx = refine_pic_friend_msg(ctx)
            if pic_ctx is not None:
                content = pic_ctx.Content
            else:
                content = ctx.Content
            if content == string:
                return func(ctx)
            return None

        return inner

    return deco
