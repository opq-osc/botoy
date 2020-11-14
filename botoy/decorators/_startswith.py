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
            if refine_ctx is not None:
                content = refine_ctx.Content
            else:
                content = ctx.Content
            # 这里的content按理永远不可能为None，但就是碰到了这种情况，startswith用得比较多
            # 所以先在这里增加一步判断
            if content is not None and content.startswith(string):
                return func(ctx)
            return None

        return inner

    return deco
