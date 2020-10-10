import re

from ..model import FriendMsg, GroupMsg
from ..refine import refine_pic_friend_msg, refine_pic_group_msg


def in_content(string: str, raw: bool = True):
    """Content字段包括指定字符串  GroupMsg, FriendMsg

    :param string: 需要包含的字符串, 支持使用正则查找
    :param raw: 为True则使用最原始的Content字段数据进行查找, 即图片这类消息会包含图片链接、
                图片MD5之类的数据; 为False则会提取真正发送的文字部分内容
    """

    def deco(func):
        def inner(ctx):
            assert isinstance(ctx, (GroupMsg, FriendMsg))
            if raw:
                if re.match(string, ctx.Content):
                    return func(ctx)
            else:
                if isinstance(ctx, GroupMsg):
                    pic_ctx = refine_pic_group_msg(ctx)
                else:
                    pic_ctx = refine_pic_friend_msg(ctx)
                if pic_ctx is not None:
                    content = pic_ctx.Content
                else:
                    content = ctx.Content
                if re.match(string, content):
                    return func(ctx)
            return None

        return inner

    return deco
