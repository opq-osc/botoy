from ..model import FriendMsg, GroupMsg
from ..parser import friend as fp
from ..parser import group as gp


def startswith(string: str):
    """Content以指定前缀开头  GroupMsg, FriendMsg
    :param string: 前缀字符串, 会解析图片消息的Content
    """

    def deco(func):
        def inner(ctx):
            assert isinstance(ctx, (GroupMsg, FriendMsg))
            if isinstance(ctx, GroupMsg):
                pic_data = gp.pic(ctx)
            else:
                pic_data = fp.pic(ctx)
            if pic_data is not None:
                content = pic_data.Content
            else:
                content = ctx.Content
            # 这里的content按理永远不可能为None，但就是碰到了这种情况，startswith用得比较多
            # 所以先在这里增加一步判断
            if content is not None and content.startswith(string):
                return func(ctx)
            return None

        return inner

    return deco
