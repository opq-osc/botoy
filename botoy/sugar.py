# pylint: disable=W0212
"""深度封装发送操作"""
import inspect
import re
from pathlib import Path
from typing import List, Optional, Tuple, Type, Union

from . import macro
from .action import Action
from .collection import MsgTypes
from .log import logger
from .model import FriendMsg, GroupMsg
from .utils import file_to_base64

_T_Data = Union[str, Path, List[str]]

_BASE64_REGEX = re.compile(
    r"^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{4}|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)$"
)


def find_local(back_stack: int = 1) -> Tuple[Union[FriendMsg, GroupMsg], Action]:
    back = inspect.currentframe().f_back  # type: ignore
    for _ in range(back_stack):
        back = back.f_back  # type: ignore
    locals = back.f_locals  # type: ignore

    ctx = locals.get("ctx")
    if not isinstance(ctx, (FriendMsg, GroupMsg)):
        for v in locals.values():
            if isinstance(v, (GroupMsg, FriendMsg)):
                ctx = v
                break

    # FIXME: 更好的处理方式
    assert ctx is not None  # 这里应该是不可能发生的

    if hasattr(ctx, "_host") and hasattr(ctx, "_port"):
        action = Action(
            ctx.CurrentQQ,
            host=getattr(ctx, "_host"),
            port=getattr(ctx, "_port"),
        )
    else:
        action = Action(ctx.CurrentQQ)
    logger.debug(
        f"find locals: ctx => {id(ctx)} host => {action.config.host} port => {action.config.port}"
    )
    return (ctx, action)


def Text(text: str, at=False):
    """发送文字
    :param text: 文字内容
    :param at: 是否艾特发送该消息的用户
    """
    text = str(text)

    ctx, action = find_local()

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


def Picture(pic_url="", pic_base64="", pic_path="", pic_md5="", text=""):
    """发送图片 经支持群消息和好友消息接收函数内调用
    :param pic_url: 图片链接
    :param pic_base64: 图片base64编码
    :param pic_path: 图片文件路径
    :param pic_md5: 已发送图片的MD5, 如果是发给群聊，可以传入图片MD5列表
    :param text: 包含的文字消息

    ``pic_url, pic_base64, pic_path必须给定一项``
    """
    assert any([pic_url, pic_base64, pic_path, pic_md5]), "必须给定一项"

    ctx, action = find_local()

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
            return action.sendGroupPic(ctx.FromGroupId, content=text, picMd5s=pic_md5)

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


def Voice(voice_url="", voice_base64="", voice_path=""):
    """发送语音 经支持群消息和好友消息接收函数内调用
    :param voice_url: 语音链接
    :param voice_base64: 语音base64编码
    :param voice_path: 语音文件路径

    voice_url, voice_base64, voice_path必须给定一项
    """
    assert any([voice_url, voice_base64, voice_path]), "必须给定一项"

    ctx, action = find_local()

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


class S:
    TYPE_AUTO: int = 0
    TYPE_URL: int = 1
    TYPE_BASE64: int = 2
    TYPE_MD5: int = 3
    TYPE_PATH: int = 4

    _locals: Optional[Tuple[Union[FriendMsg, GroupMsg], Action]] = None

    @classmethod
    def bind(cls, ctx: Union[FriendMsg, GroupMsg]) -> Type["S"]:
        """绑定该上下文对象，获取一个与该上下文对应的新的S"""
        if hasattr(ctx, "_host") and hasattr(ctx, "_port"):
            action = Action(
                ctx.CurrentQQ,
                host=getattr(ctx, "_host"),
                port=getattr(ctx, "_port"),
            )
        else:
            action = Action(ctx.CurrentQQ)

        return type("S", (S,), dict(_locals=(ctx, action)))

    @classmethod
    def __guess_data_type(cls, data: _T_Data) -> int:
        # FIXME: if hell. 逻辑并不严谨
        # url, path, md5, base64
        # url
        #   http:// 或 https:// 开头的肯定是
        # path
        #   1. Path => 确定
        #   2. str => 用常规经验判断
        #       a. 本地路径一般不可能超过 1000 吧
        #       b. 文件存在
        # md5
        #   1. List[str] => 确定
        #   2. str 目前来看，opq收到的图片MD5均是长度为24，==结尾，
        #   语音并不支持md5发送, 基本可以确定, 并且一张图片的base64不可能这么短

        # Path, List[str]
        if isinstance(data, Path):  # Path 特殊对象优先判断
            return cls.TYPE_PATH
        elif isinstance(data, list):  # 必定为MD5
            return cls.TYPE_MD5
        # 处理 str
        elif data.startswith("http://") or data.startswith("https://"):
            return cls.TYPE_URL
        elif len(data) == 24 and data.endswith("=="):
            return cls.TYPE_MD5
        elif len(data) < 1000:
            if Path(data).exists():
                return cls.TYPE_PATH
            elif re.match(_BASE64_REGEX, data):
                return cls.TYPE_BASE64
            # else:
            #     return cls.TYPE_MD5
        elif re.match(_BASE64_REGEX, data):
            return cls.TYPE_BASE64

        assert False, "正常情况下这里应该是执行不到的"

    @classmethod
    def text(cls, text: str, at: bool = False):
        """发送文字
        :param text: 发送的文字内容
        :param at: 是否要艾特该用户
        """
        logger.debug(f"_locals =>  {cls._locals}")
        if cls._locals:
            logger.debug("已存在locals")
            ctx, action = cls._locals
        else:
            ctx, action = find_local()

        if isinstance(ctx, GroupMsg):
            logger.debug("发送群聊文字")
            return action.sendGroupText(
                ctx.FromGroupId, text, atUser=ctx.FromUserId if at else 0
            )
        elif isinstance(ctx, FriendMsg):
            if ctx.TempUin:
                logger.debug("发送私聊文字")
                return action.sendPrivateText(ctx.FromUin, ctx.TempUin, text)
            elif ctx.MsgType == MsgTypes.PhoneMsg:
                logger.debug("发送手机文字")
                return action.sendPhoneText(text)
            else:
                logger.debug("发送好友文字")
                return action.sendFriendText(ctx.FromUin, text)
        return None

    @classmethod
    def image(cls, data: _T_Data, text: str = "", at: bool = False, type: int = 0):
        """发送图片
        :param data: 发送的内容, 可以为 路径字符串或路径Path对象， 可以为网络(URL)地址,
        或者 base64 字符串，或者为MD5或MD5列表，当为MD5列表(发送多图)时，参数text将无效

        :param text: 图片附带的文字信息
        :param at: 是否要艾特该用户
        :param type: 发送内容的类型, 默认自动判断，可选值为 S.TYPE_?
        """
        if cls._locals:
            ctx, action = cls._locals
        else:
            ctx, action = find_local()

        if type not in (
            cls.TYPE_URL,
            cls.TYPE_MD5,
            cls.TYPE_BASE64,
            cls.TYPE_PATH,
        ):
            type = cls.__guess_data_type(data)

        if isinstance(ctx, GroupMsg):
            if at:
                text = macro.atUser(ctx.FromUserId) + text

            if type == cls.TYPE_URL:
                logger.debug("发送群聊网络图片")
                return action.sendGroupPic(ctx.FromGroupId, content=text, picUrl=data)  # type: ignore
            elif type == cls.TYPE_BASE64:
                logger.debug("发送群聊base64图片")
                return action.sendGroupPic(ctx.FromGroupId, content=text, picBase64Buf=data)  # type: ignore
            elif type == cls.TYPE_MD5:
                logger.debug("发送群聊md5图片")
                return action.sendGroupPic(
                    ctx.FromGroupId, content=text, picMd5s=data  # type:ignore
                )
            elif type == cls.TYPE_PATH:
                logger.debug("发送群聊本地图片")
                return action.sendGroupPic(
                    ctx.FromGroupId, content=text, picBase64Buf=file_to_base64(data)
                )
        elif isinstance(ctx, FriendMsg):
            if ctx.TempUin:
                if type == cls.TYPE_URL:
                    logger.debug("发送私聊网络图片")
                    return action.sendPrivatePic(
                        ctx.FromUin, ctx.TempUin, content=text, picUrl=data  # type: ignore
                    )
                elif type == cls.TYPE_BASE64:
                    logger.debug("发送私聊base64图片")
                    return action.sendPrivatePic(
                        ctx.FromUin, ctx.TempUin, content=text, picBase64Buf=data  # type: ignore
                    )
                elif type == cls.TYPE_MD5:
                    logger.debug("发送私聊md5图片")
                    return action.sendPrivatePic(
                        ctx.FromUin,
                        ctx.TempUin,
                        content=text,
                        fileMd5=data,  # type:ignore
                    )
                elif type == cls.TYPE_PATH:
                    logger.debug("发送私聊本地图片")
                    return action.sendPrivatePic(
                        ctx.FromUin, ctx.TempUin, content=text, picBase64Buf=file_to_base64(data)  # type: ignore
                    )
            else:
                if type == cls.TYPE_URL:
                    logger.debug("发送好友链接图片")
                    return action.sendFriendPic(ctx.FromUin, content=text, picUrl=data)  # type: ignore
                elif type == cls.TYPE_BASE64:
                    logger.debug("发送好友base64图片")
                    return action.sendFriendPic(ctx.FromUin, content=text, picBase64Buf=data)  # type: ignore
                elif type == cls.TYPE_MD5:
                    logger.debug("发送好友md5图片")
                    return action.sendFriendPic(ctx.FromUin, content=text, fileMd5=data)  # type: ignore
                elif type == cls.TYPE_PATH:
                    logger.debug("发送好友本地图片")
                    return action.sendFriendPic(ctx.FromUin, content=text, picBase64Buf=file_to_base64(data))  # type: ignore

        return None

    @classmethod
    def voice(cls, data: _T_Data, type: int = 0):
        """发送语音
        :param data: 发送的内容, 可以为 路径字符串或路径Path对象， 可以为网络(URL)地址,
        或者 base64 字符串， 不支持MD5

        :param type: 发送内容的类型, 默认自动判断，可选值为 S.TYPE_?
        """
        if cls._locals:
            ctx, action = cls._locals
        else:
            ctx, action = find_local()

        if type not in (
            cls.TYPE_URL,
            cls.TYPE_MD5,
            cls.TYPE_BASE64,
            cls.TYPE_PATH,
        ):
            type = cls.__guess_data_type(data)

        assert type != cls.TYPE_MD5, "语音不支持MD5发送"

        if isinstance(ctx, GroupMsg):
            if type == cls.TYPE_URL:
                logger.debug("发送群聊网络语音")
                return action.sendGroupVoice(ctx.FromGroupId, voiceUrl=data)  # type: ignore
            elif type == cls.TYPE_BASE64:
                logger.debug("发送群聊base64语音")
                return action.sendGroupVoice(ctx.FromGroupId, voiceBase64Buf=data)  # type: ignore
            elif type == cls.TYPE_PATH:
                logger.debug("发送群聊本地语音")
                return action.sendGroupVoice(ctx.FromGroupId, voiceBase64Buf=file_to_base64(data))  # type: ignore

        elif isinstance(ctx, FriendMsg):
            if ctx.TempUin:
                if type == cls.TYPE_URL:
                    logger.debug("发送私聊网络语音")
                    return action.sendPrivateVoice(
                        ctx.FromUin, ctx.TempUin, voiceUrl=data  # type: ignore
                    )
                elif type == cls.TYPE_BASE64:
                    logger.debug("发送私聊base64语音")
                    return action.sendPrivateVoice(
                        ctx.FromUin, ctx.TempUin, voiceBase64Buf=data  # type: ignore
                    )
                elif type == cls.TYPE_PATH:
                    logger.debug("发送私聊本地语音")
                    return action.sendPrivateVoice(
                        ctx.FromUin, ctx.TempUin, voiceBase64Buf=file_to_base64(data)  # type: ignore
                    )
            else:
                if type == cls.TYPE_URL:
                    logger.debug("发送好友网络语音")
                    return action.sendFriendVoice(ctx.FromUin, voiceUrl=data)  # type: ignore
                elif type == cls.TYPE_BASE64:
                    logger.debug("发送好友base64语音")
                    return action.sendFriendVoice(ctx.FromUin, voiceBase64Buf=data)  # type: ignore
                elif type == cls.TYPE_PATH:
                    logger.debug("发送好友本地语音")
                    return action.sendFriendVoice(ctx.FromUin, voiceBase64Buf=file_to_base64(data))  # type: ignore

        return None
