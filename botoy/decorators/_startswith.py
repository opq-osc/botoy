from ..model import FriendMsg, GroupMsg
from ..refine import refine_pic_friend_msg, refine_pic_group_msg


def startswith(string: str):
    """Content以指定前缀开头  GroupMsg, FriendMsg
    :param string: 前缀字符串, 会解析图片消息的Content
    """

    def deco(func):
        def inner(ctx):
            assert isinstance(ctx, (GroupMsg, FriendMsg))
            if isinstance(ctx, GroupMsg):
                refine_ctx = refine_pic_group_msg(ctx)  # type: _PicGroupMsg
            else:
                refine_ctx = refine_pic_friend_msg(ctx)  # type:_PicFriendMsg
            content = refine_ctx.Content  # type:str
            if refine_ctx is not None:
                content = refine_ctx.Content
            else:
                content = ctx.Content
            if content.startswith(string):
                return func(ctx)
            return None

        return inner

    return deco
