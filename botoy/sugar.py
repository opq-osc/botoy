# pylint: disable=W0212
"""深度封装Action方法
函数只能在群消息和好友消息接收函数中调用
"""
import sys

from .action import Action
from .collection import MsgTypes
from .exceptions import InvalidContextError
from .model import FriendMsg, GroupMsg
from .util import file_to_base64


def Text(text: str, at=False):
    """发送文字
    :param text: 文字内容
    :param at:是否艾特发送该消息的用户
    """
    text = str(text)
    # 查找消息上下文 `ctx`变量
    ctx = None
    f = sys._getframe()
    upper = f.f_back
    upper_locals = upper.f_locals
    if 'ctx' in upper_locals and isinstance(upper_locals['ctx'], (FriendMsg, GroupMsg)):
        ctx = upper_locals['ctx']
    else:
        for v in upper_locals.values():
            if isinstance(v, (GroupMsg, FriendMsg)):
                ctx = v
                break
    if ctx is None:
        raise InvalidContextError('经支持群消息和好友消息接收函数内调用')

    if hasattr(ctx, '_host') and hasattr(ctx, '_port'):
        action = Action(ctx.CurrentQQ, port=ctx._port, host=ctx._host)
    else:
        action = Action(ctx.CurrentQQ)

    if isinstance(ctx, GroupMsg):
        return action.sendGroupText(
            ctx.FromGroupId, text, atUser=ctx.FromUserId if at else 0
        )
    if isinstance(ctx, FriendMsg):
        if ctx.TempUin:  # 私聊消息
            return action.sendPrivateText(ctx.FromUin, ctx.TempUin, text)
        elif ctx.MsgType == MsgTypes.PhoneMsg:  # 来自手机的消息
            return action.sendPhoneText(text)
        else:
            return action.sendFriendText(ctx.FromUin, text)
    return None


def Picture(pic_url='', pic_base64='', pic_path='', pic_md5='', text=''):
    """发送图片 经支持群消息和好友消息接收函数内调用
    :param pic_url: 图片链接
    :param pic_base64: 图片base64编码
    :param pic_path: 图片文件路径
    :param pic_md5: 已发送图片的MD5
    :param text: 包含的文字消息

    ``pic_url, pic_base64, pic_path必须给定一项``
    """
    assert any([pic_url, pic_base64, pic_path, pic_md5]), '必须给定一项'

    ctx = None
    f = sys._getframe()
    upper = f.f_back
    upper_locals = upper.f_locals
    if 'ctx' in upper_locals and isinstance(upper_locals['ctx'], (FriendMsg, GroupMsg)):
        ctx = upper_locals['ctx']
    else:
        for v in upper_locals.values():
            if isinstance(v, (FriendMsg, GroupMsg)):
                ctx = v
                break
    if ctx is None:
        raise InvalidContextError('经支持群消息和好友消息接收函数内调用')

    if hasattr(ctx, '_host') and hasattr(ctx, '_port'):
        action = Action(ctx.CurrentQQ, port=ctx._port, host=ctx._host)
    else:
        action = Action(ctx.CurrentQQ)

    if isinstance(ctx, GroupMsg):
        if pic_url:
            return action.sendGroupPic(ctx.FromGroupId, content=text, picUrl=pic_url)

        elif pic_base64:
            return action.sendGroupPic(
                ctx.FromGroupId, content=text, picBase64Buf=pic_base64
            )
        elif pic_path:
            return action.sendGroupPic(
                ctx.FromGroupId, content=text, picBase64Buf=file_to_base64(pic_path)
            )
        elif pic_md5:
            return action.sendGroupPic(ctx.FromGroupId, content=text, fileMd5=pic_md5)

    if isinstance(ctx, FriendMsg):
        if pic_url:
            if ctx.TempUin is not None:
                return action.sendPrivatePic(
                    ctx.FromUin, ctx.TempUin, content=text, picUrl=pic_url
                )
            else:
                return action.sendFriendPic(ctx.FromUin, picUrl=pic_url, content=text)
        elif pic_base64:
            if ctx.TempUin:
                return action.sendPrivatePic(
                    ctx.FromUin, ctx.TempUin, content=text, picBase64Buf=pic_base64
                )
            elif ctx.MsgType == MsgTypes.PhoneMsg:  # 来自手机的消息
                return None
            else:
                return action.sendFriendPic(
                    ctx.FromUin, picBase64Buf=pic_base64, content=text
                )
        elif pic_path:
            if ctx.TempUin:
                return action.sendPrivatePic(
                    ctx.FromUin,
                    ctx.TempUin,
                    content=text,
                    picBase64Buf=file_to_base64(pic_path),
                )
            elif ctx.MsgType == MsgTypes.PhoneMsg:  # 来自手机的消息
                return None
            else:
                return action.sendFriendPic(
                    ctx.FromUin, picBase64Buf=file_to_base64(pic_path), content=text
                )
        elif pic_md5:
            if ctx.TempUin:
                return action.sendPrivatePic(
                    ctx.FromUin, ctx.TempUin, content=text, fileMd5=pic_md5
                )
            elif ctx.MsgType == MsgTypes.PhoneMsg:  # 来自手机的消息
                return None
            else:
                return action.sendFriendPic(ctx.FromUin, fileMd5=pic_md5, content=text)
    return None


def Voice(voice_url='', voice_base64='', voice_path=''):
    """发送语音 经支持群消息和好友消息接收函数内调用
    :param voice_url: 语音链接
    :param voice_base64: 语音base64编码
    :param voice_path: 语音文件路径
    voice_url, voice_base64, voice_path必须给定一项
    """
    assert any([voice_url, voice_base64, voice_path]), '必须给定一项'

    ctx = None
    f = sys._getframe()
    upper = f.f_back
    upper_locals = upper.f_locals
    if 'ctx' in upper_locals and isinstance(upper_locals['ctx'], (FriendMsg, GroupMsg)):
        ctx = upper_locals['ctx']
    else:
        for v in upper_locals.values():
            if isinstance(v, (GroupMsg, FriendMsg)):
                ctx = v
                break
    if ctx is None:
        raise InvalidContextError('经支持群消息和好友消息接收函数内调用')

    if hasattr(ctx, '_host') and hasattr(ctx, '_port'):
        action = Action(ctx.CurrentQQ, port=ctx._port, host=ctx._host)
    else:
        action = Action(ctx.CurrentQQ)

    if isinstance(ctx, GroupMsg):
        if voice_url:
            return action.sendGroupVoice(ctx.FromGroupId, voiceUrl=voice_url)
        elif voice_base64:
            return action.sendGroupVoice(ctx.FromGroupId, voiceBase64Buf=voice_base64)
        elif voice_path:
            return action.sendGroupVoice(
                ctx.FromGroupId, voiceBase64Buf=file_to_base64(voice_path)
            )
    if isinstance(ctx, FriendMsg):
        if voice_url:
            if ctx.TempUin:
                return action.sendPrivateVoice(
                    ctx.FromUin, ctx.TempUin, voiceUrl=voice_url
                )
            elif ctx.MsgType == MsgTypes.PhoneMsg:  # 来自手机的消息
                return None
            else:
                return action.sendFriendVoice(ctx.FromUin, voiceUrl=voice_url)
        elif voice_base64:
            if ctx.TempUin:
                return action.sendPrivateVoice(
                    ctx.FromUin, ctx.TempUin, voiceBase64Buf=voice_base64
                )
            elif ctx.MsgType == MsgTypes.PhoneMsg:  # 来自手机的消息
                return None
            else:
                return action.sendFriendVoice(ctx.FromUin, voiceBase64Buf=voice_base64)
        elif voice_path:
            if ctx.TempUin:
                return action.sendPrivateVoice(
                    ctx.FromUin, ctx.TempUin, voiceBase64Buf=file_to_base64(voice_path)
                )
            elif ctx.MsgType == MsgTypes.PhoneMsg:  # 来自手机的消息
                return None
            else:
                return action.sendFriendVoice(
                    ctx.FromUin, voiceBase64Buf=file_to_base64(voice_path)
                )
    return None
