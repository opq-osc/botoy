import re
from typing import List, Optional, Union

from ..collection import MsgTypes
from ..model import FriendMsg, GroupMsg


def common_text(
    func=None,
    equal: Optional[str] = None,
    in_: Optional[str] = None,
    starts: Optional[str] = None,
    ends: Optional[str] = None,
    user: Optional[Union[int, List[int]]] = None,
    group: Optional[Union[int, List[int]]] = None,
    ignore_user: Optional[Union[int, List[int]]] = None,
    ignore_group: Optional[Union[int, List[int]]] = None,
    ignore_bot=True,
):
    """常见对文字消息的处理(不考虑私聊消息) GroupMsg,FriendMsg
    :param equal: 内容需要相等(==)
    :param in_: 内容需要包含，该项支持正则表达式(re.findall)
    :param starts: 内容以该项开头(startswith)
    :param ends: 内容以该项结尾(endswith)
    :param user: 来自该用户(们)(in)
    :param group: 来自该群组(们)(in)
    :param ignore_user: 忽略该用户(们)(not in)
    :param ignore_group: 忽略该群组(们)(not in)
    :param ignore_bot: 忽略机器人自身
    """
    if func is None:
        return common_text

    async def inner(ctx):
        assert isinstance(ctx, (GroupMsg, FriendMsg))
        if ctx.MsgType != MsgTypes.TextMsg:
            return
        if isinstance(ctx, GroupMsg):
            if ignore_bot:
                if ctx.FromUserId == ctx.CurrentQQ:
                    return
            if equal is not None:
                if ctx.Content != equal:
                    return
            if in_ is not None:
                if not re.findall(in_, ctx.Content):
                    return
            if starts is not None:
                if not ctx.Content.startswith(starts):
                    return
            if ends is not None:
                if not ctx.Content.endswith(ends):
                    return
            if user is not None:
                if isinstance(user, int):
                    users = [user]
                else:
                    users = user
                if ctx.FromUserId not in users:
                    return
            if group is not None:
                if isinstance(group, int):
                    groups = [group]
                else:
                    groups = group
                if ctx.FromGroupId not in groups:
                    return
            if ignore_user is not None:
                if isinstance(ignore_user, int):
                    iusers = [ignore_user]
                else:
                    iusers = ignore_user
                if ctx.FromUserId in iusers:
                    return
            if ignore_group is not None:
                if isinstance(ignore_group, int):
                    igroups = [ignore_group]
                else:
                    igroups = ignore_group
                if ctx.FromGroupId in igroups:
                    return

        else:
            if ctx.TempUin:
                return

            if ignore_bot:
                if ctx.FromUin == ctx.CurrentQQ:
                    return
            if equal is not None:
                if ctx.Content != equal:
                    return
            if in_ is not None:
                if not re.findall(in_, ctx.Content):
                    return
            if starts is not None:
                if not ctx.Content.startswith(starts):
                    return
            if ends is not None:
                if not ctx.Content.endswith(ends):
                    return
            if user is not None:
                if isinstance(user, int):
                    users = [user]
                else:
                    users = user
                if ctx.FromUin not in users:
                    return
            if ignore_user is not None:
                if isinstance(ignore_user, int):
                    iusers = [ignore_user]
                else:
                    iusers = ignore_user
                if ctx.FromUin in iusers:
                    return
        return await func(ctx)

    return inner
