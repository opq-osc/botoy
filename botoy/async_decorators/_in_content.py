import re

from ..model import FriendMsg, GroupMsg
from ..parser import friend as fp
from ..parser import group as gp


def in_content(string: str, raw: bool = True):
    """Content字段包括指定字符串  GroupMsg, FriendMsg

    :param string: 需要包含的字符串, 支持使用正则查找
    :param raw: 为True则使用最原始的Content字段数据进行查找, 即图片这类消息会包含图片链接、
                图片MD5之类的数据; 为False则会提取真正发送的文字部分内容
    """

    def deco(func):
        async def inner(ctx):
            assert isinstance(ctx, (GroupMsg, FriendMsg))
            if raw:
                if re.findall(string, ctx.Content):
                    return await func(ctx)
            else:
                if isinstance(ctx, GroupMsg):
                    pic_data = gp.pic(ctx)
                else:
                    pic_data = fp.pic(ctx)
                if pic_data is not None:
                    content = pic_data.Content
                else:
                    content = ctx.Content
                if re.findall(string, content):
                    return await func(ctx)

        return inner

    return deco
