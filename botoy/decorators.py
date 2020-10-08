# pylint:disable=W0613
"""提供辅助构建接收函数的装饰器"""
import copy
import re

from botoy import json
from botoy.collections import MsgTypes
from botoy.model import FriendMsg, GroupMsg
from botoy.refine import (
    _PicFriendMsg,
    _PicGroupMsg,
    refine_pic_friend_msg,
    refine_pic_group_msg
)


def startswith(string: str, trim=True):
    """content以指定前缀开头时
    :param string: 前缀字符串
    :param trim: 是否将原始Content部分替换为裁剪掉前缀的内容
    """

    def deco(func):
        def inner(ctx):
            if isinstance(ctx, (GroupMsg, FriendMsg)):
                if isinstance(ctx, GroupMsg):
                    refine_ctx = refine_pic_group_msg(ctx)  # type: _PicGroupMsg
                else:
                    refine_ctx = refine_pic_friend_msg(ctx)  # type:_PicFriendMsg
                content = refine_ctx.Content  # type:str
                if content.startswith(string):
                    # 不需要裁剪，直接传入原始ctx
                    if not trim:
                        return func(ctx)
                    # 需要裁剪
                    # 处理完图片消息中的Content后，需重新编码为字符串，保证传入接收函数ctx一致性
                    new_content = content[len(string) :]
                    if ctx.MsgType == MsgTypes.PicMsg:
                        raw_content_data = json.loads(ctx.Content)
                        raw_content_data['Content'] = new_content
                        ctx.Content = json.dumps(raw_content_data, ensure_ascii=False)
                    else:
                        ctx.Content = new_content
                    return func(ctx)
            return None

        return inner

    return deco


def in_content(string: str):
    """
    接受消息content字段含有指定消息时, 不支持事件类型消息
    :param string: 支持正则
    """

    def deco(func):
        def inner(ctx):
            if isinstance(ctx, (GroupMsg, FriendMsg)):
                if re.search(string, ctx.Content):
                    return func(ctx)
            return None

        return inner

    return deco


def equal_content(string: str):
    """
    content字段与指定消息相等时, 不支持事件类型消息
    """

    def deco(func):
        def inner(ctx):
            if isinstance(ctx, (GroupMsg, FriendMsg)):
                new_ctx = copy.deepcopy(ctx)
                if isinstance(ctx, GroupMsg):
                    if ctx.MsgType == MsgTypes.PicMsg:
                        new_ctx = refine_pic_group_msg(new_ctx)
                else:
                    if ctx.MsgType == MsgTypes.PicMsg:
                        new_ctx = refine_pic_friend_msg(new_ctx)
                if new_ctx.Content == string:
                    return func(ctx)
            return None

        return inner

    return deco


def ignore_botself(func=None):
    """忽略机器人自身的消息"""
    if func is None:
        return ignore_botself

    def inner(ctx):
        if isinstance(ctx, (GroupMsg, FriendMsg)):
            if isinstance(ctx, GroupMsg):
                userid = ctx.FromUserId
            else:
                userid = ctx.FromUin
            if userid != ctx.CurrentQQ:
                return func(ctx)
        return None

    return inner


def is_botself(func=None):
    """只要机器人自身的消息"""
    if func is None:
        return is_botself

    def inner(ctx):
        if isinstance(ctx, (GroupMsg, FriendMsg)):
            if isinstance(ctx, GroupMsg):
                userid = ctx.FromUserId
            else:
                userid = ctx.FromUin
            if userid == ctx.CurrentQQ:
                return func(ctx)
        return None

    return inner


def not_these_users(users: list):
    """不接受这些人的消息
    :param users: qq号列表
    """

    def deco(func):
        def inner(ctx):
            nonlocal users
            if isinstance(ctx, (GroupMsg, FriendMsg)):
                if not hasattr(users, '__iter__'):
                    users = [users]
                if isinstance(ctx, GroupMsg):
                    from_user = ctx.FromUserId
                elif isinstance(ctx, FriendMsg):
                    from_user = ctx.FromUin
                if from_user not in users:
                    return func(ctx)
            return None

        return inner

    return deco


def only_these_users(users: list):
    """仅接受这些人的消息
    :param users: qq号列表
    """

    def deco(func):
        def inner(ctx):
            nonlocal users
            if isinstance(ctx, (GroupMsg, FriendMsg)):
                if not hasattr(users, '__iter__'):
                    users = [users]
                if isinstance(ctx, GroupMsg):
                    from_user = ctx.FromUserId
                elif isinstance(ctx, FriendMsg):
                    from_user = ctx.FromUin
                if from_user in users:
                    return func(ctx)
            return None

        return inner

    return deco


def only_this_msg_type(msg_type: str):
    """仅接受该类型消息
    :param msg_type: TextMsg, PicMsg, AtMsg, ReplyMsg, VoiceMsg之一
    """

    def deco(func):
        def inner(ctx):
            if isinstance(ctx, (GroupMsg, FriendMsg)):
                if ctx.MsgType == msg_type:
                    return func(ctx)
            return None

        return inner

    return deco


def not_these_groups(groups: list):
    """不接受这些群组的消息
    :param groups: 群号列表
    """

    def deco(func):
        def inner(ctx):
            nonlocal groups
            if isinstance(ctx, GroupMsg):
                if not hasattr(groups, '__iter__'):
                    groups = [groups]
                from_group = ctx.FromGroupId
                if from_group not in groups:
                    return func(ctx)
            return None

        return inner

    return deco


def only_these_groups(groups: list):
    """只接受这些群组的消息
    :param groups: 群号列表
    """

    def deco(func):
        def inner(ctx):
            nonlocal groups
            if isinstance(ctx, GroupMsg):
                if not hasattr(groups, '__iter__'):
                    groups = [groups]
                from_group = ctx.FromGroupId
                if from_group in groups:
                    return func(ctx)
            return None

        return inner

    return deco
