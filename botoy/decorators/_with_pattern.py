import re

from ..model import FriendMsg, GroupMsg


def with_pattern(pattern: str):
    """正则匹配Content字段 GroupMsg, FriendMsg
    因为使用这种功能一般匹配的内容都比较特殊,像图片，视频之类的消息基本是不会符合匹配条件的,
    所以不会解析特殊的消息, 均采用最原始的Content字段进行匹配,

    注意: 成功匹配才会执行该接收函数,匹配到的结果是一个列表,该结果会增加为ctx的``_pattern_result``属性

    :param pattern: 需要进行匹配的``正则表达式字符串``
    """

    def deco(func):
        def inner(ctx):
            assert isinstance(ctx, (GroupMsg, FriendMsg))
            result = re.findall(pattern, ctx.Content)
            if result:
                ctx._pattern_result = result  # pylint: disable=W0212
                return func(ctx)
            return None

        return inner

    return deco
