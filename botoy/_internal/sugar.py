# pylint: disable=W0212
"""深度封装发送操作"""
import base64
import re
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple, Union

from .action import Action
from .context import Context
from .context import ctx as current_ctx
from .utils import file_to_base64

# str => base64, md5, file path
# bytes => base64
# BytesIO =>base64
# BinaryIO => base64
# Path => file path
# List[str] => md5 list
_T_Data = Union[str, bytes, BytesIO, BinaryIO, Path, List[str]]

_BASE64_REGEX = re.compile(
    r"^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{4}|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)$"
)

TYPE_AUTO: int = 0
TYPE_URL: int = 1
TYPE_BASE64: int = 2
TYPE_MD5: int = 3
TYPE_PATH: int = 4


def _resolve_data_type(data: _T_Data) -> Tuple[int, _T_Data]:
    """用来处理数据类型，必要时需要对数据进行进一步加工再返回"""
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

    # base64
    #   1. 前面都不符合剩余的情况就是base64
    #   2. bytes 一定是base64
    #   3. base64:// 开头

    # Path, List[str]

    type = None

    if isinstance(data, Path):  # Path 特殊对象优先判断
        type = TYPE_PATH
    elif isinstance(data, bytes):  # bytes 必定是base64
        type = TYPE_BASE64
        data = base64.b64encode(data).decode()
    elif isinstance(data, BytesIO):
        type = TYPE_BASE64
        data = base64.b64encode(data.getvalue()).decode()
    elif isinstance(data, BinaryIO):
        type = TYPE_BASE64
        data = base64.b64encode(data.read()).decode()
    elif isinstance(data, list):  # 必定为MD5
        type = TYPE_MD5
    # 处理 str
    elif data.startswith("http://") or data.startswith("https://"):
        type = TYPE_URL
    elif data.startswith("base64://"):
        type = TYPE_BASE64
        data = data[9:]
    elif len(data) == 24 and data.endswith("=="):
        type = TYPE_MD5
    elif len(data) < 1000:
        if Path(data).exists():
            type = TYPE_PATH
        elif re.match(_BASE64_REGEX, data):
            type = TYPE_BASE64
        # else:
        #     return cls.TYPE_MD5
    elif re.match(_BASE64_REGEX, data):
        type = TYPE_BASE64

    if type is not None:
        return type, data

    assert False, "正常情况下这里应该是执行不到的"


class _S:
    # 为了便捷调用这些常数和兼容
    TYPE_AUTO = TYPE_AUTO
    TYPE_URL = TYPE_URL
    TYPE_BASE64 = TYPE_BASE64
    TYPE_MD5 = TYPE_MD5
    TYPE_PATH = TYPE_PATH

    def __init__(self, ctx: Optional[Context] = None):
        if ctx:
            # 调用bind才有这一步
            self._g_msg = ctx.group_msg
            self._f_msg = ctx.friend_msg
            if not self.g_msg and not self.f_msg:
                raise ValueError("ctx不合法，此处不符合常理，请反馈!")
        else:
            self._g_msg = None
            self._f_msg = None

    @property
    def g_msg(self):
        # 没调用bind，这里必为None
        return self._g_msg or current_ctx.g

    @property
    def f_msg(self):
        return self._f_msg or current_ctx.f

    def bind(self, ctx: Context) -> "_S":
        """绑定该上下文对象，获取一个与该上下文对应的新的S"""
        return _S(ctx)

    async def text(self, text: str, at: bool = False):
        """发送文字
        :param text: 发送的文字内容
        :param at: 是否要艾特该用户
        """
        # TODO: ctx中附带连接地址等信息, 在此处处理
        action = Action((self.g_msg or self.f_msg).bot_qq)  # type: ignore
        async with action:
            if g := self.g_msg:
                return await action.sendGroupText(
                    g.from_group,
                    text,
                    atUser=g.sender_uin if at else 0,
                    atUserNick=g.sender_nick,
                )
            elif f := self.f_msg:
                if f.msg_type == 141: # NOTE: 私聊
                    return await action.sendPrivateText(f.from_user,f.from_group, text)
                elif f.is_from_phone:
                    return await action.sendPhoneText(text)
                else:
                    return await action.sendFriendText(f.from_user, text)
            return None

    #
    async def image(
        self, data: _T_Data, text: str = "", at: bool = False, type: int = 0
    ):
        """发送图片
        :param data: 发送的内容, 可以为 路径字符串或路径Path对象， 可以为网络(URL)地址,
        或者 base64 字符串, 或者为bytes(此时为base64)，或者为MD5或MD5列表，当为MD5列表(发送多图)时，参数text将无效

        :param text: 图片附带的文字信息
        :param at: 是否要艾特该用户
        :param type: 发送内容的类型, 默认自动判断，可选值为 S.TYPE_?
        """

        if type not in (
            TYPE_URL,
            TYPE_MD5,
            TYPE_BASE64,
            TYPE_PATH,
        ):
            type, data = _resolve_data_type(data)

        action = Action((self.g_msg or self.f_msg).bot_qq)  # type: ignore
        async with action:
            if g := self.g_msg:
                atUser = g.sender_uin if at else 0

                if type == TYPE_URL:
                    return await action.sendGroupPic(
                        g.from_group,
                        text=text,
                        url=data,  # type:ignore
                        atUser=atUser,
                        atUserNick=g.sender_nick,
                    )
                elif type == TYPE_BASE64:
                    return await action.sendGroupPic(
                        g.from_group,
                        text=text,
                        base64=data,  # type: ignore
                        atUser=atUser,
                        atUserNick=g.sender_nick,
                    )
                elif type == TYPE_MD5:
                    return await action.sendGroupPic(
                        g.from_group,
                        text=text,
                        md5=data,  # type:ignore
                        atUser=atUser,
                        atUserNick=g.sender_nick,
                    )
                elif type == TYPE_PATH:
                    return await action.sendGroupPic(
                        g.from_group,
                        text=text,
                        base64=file_to_base64(data),
                        atUser=atUser,
                        atUserNick=g.sender_nick,
                    )
            elif f := self.f_msg:
                if f.msg_type == 141:
                    if type == TYPE_URL:
                        return await action.sendPrivatePic(f.from_user, f.from_group,text=text, url=data)  # type: ignore
                    elif type == TYPE_BASE64:
                        return await action.sendPrivatePic(f.from_user, f.from_group, text=text, base64=data)  # type: ignore
                    elif type == TYPE_MD5:
                        return await action.sendPrivatePic(f.from_user, f.from_group,text=text, md5=data)  # type: ignore
                    elif type == TYPE_PATH:
                        return await action.sendPrivatePic(f.from_user, f.from_group,text=text, base64=file_to_base64(data))  # type: ignore
                else:
                    if type == TYPE_URL:
                        return await action.sendFriendPic(f.from_user, text=text, url=data)  # type: ignore
                    elif type == TYPE_BASE64:
                        return await action.sendFriendPic(f.from_user, text=text, base64=data)  # type: ignore
                    elif type == TYPE_MD5:
                        return await action.sendFriendPic(f.from_user, text=text, md5=data)  # type: ignore
                    elif type == TYPE_PATH:
                        return await action.sendFriendPic(f.from_user, text=text, base64=file_to_base64(data))  # type: ignore

        return None


#
#     def voice(self, data: _T_Data, type: int = 0):
#         """发送语音
#         :param data: 发送的内容, 可以为 路径字符串或路径Path对象， 可以为网络(URL)地址,
#         或者 base64 字符串, 或者为bytes(此时当作base64), 不支持MD5
#
#         :param type: 发送内容的类型, 默认自动判断，可选值为 S.TYPE_?
#         """
#         ctx = self.ctx
#         action = Action.from_ctx(ctx)
#
#         if type not in (
#             TYPE_URL,
#             TYPE_MD5,
#             TYPE_BASE64,
#             TYPE_PATH,
#         ):
#             type, data = _resolve_data_type(data)
#
#         assert type != TYPE_MD5, "语音不支持MD5发送"
#
#         if isinstance(ctx, GroupMsg):
#             if type == TYPE_URL:
#                 return action.sendGroupVoice(ctx.FromGroupId, voiceUrl=data)  # type: ignore
#             elif type == TYPE_BASE64:
#                 return action.sendGroupVoice(ctx.FromGroupId, voiceBase64Buf=data)  # type: ignore
#             elif type == TYPE_PATH:
#                 return action.sendGroupVoice(ctx.FromGroupId, voiceBase64Buf=file_to_base64(data))  # type: ignore
#
#         elif isinstance(ctx, FriendMsg):
#             if ctx.TempUin:
#                 if type == TYPE_URL:
#                     return action.sendPrivateVoice(
#                         ctx.FromUin, ctx.TempUin, voiceUrl=data  # type: ignore
#                     )
#                 elif type == TYPE_BASE64:
#                     return action.sendPrivateVoice(
#                         ctx.FromUin, ctx.TempUin, voiceBase64Buf=data  # type: ignore
#                     )
#                 elif type == TYPE_PATH:
#                     return action.sendPrivateVoice(
#                         ctx.FromUin, ctx.TempUin, voiceBase64Buf=file_to_base64(data)  # type: ignore
#                     )
#             else:
#                 if type == TYPE_URL:
#                     return action.sendFriendVoice(ctx.FromUin, voiceUrl=data)  # type: ignore
#                 elif type == TYPE_BASE64:
#                     return action.sendFriendVoice(ctx.FromUin, voiceBase64Buf=data)  # type: ignore
#                 elif type == TYPE_PATH:
#                     return action.sendFriendVoice(ctx.FromUin, voiceBase64Buf=file_to_base64(data))  # type: ignore
#
#         return None
#
#     async def atext(self, text: str, at: bool = False):
#         """发送文字
#         :param text: 发送的文字内容
#         :param at: 是否要艾特该用户
#         """
#         ctx = self.ctx
#         async with AsyncAction.from_ctx(ctx) as action:
#             if isinstance(ctx, GroupMsg):
#                 return await action.sendGroupText(
#                     ctx.FromGroupId, text, atUser=ctx.FromUserId if at else 0
#                 )
#             elif isinstance(ctx, FriendMsg):
#                 if ctx.TempUin:
#                     return await action.sendPrivateText(ctx.FromUin, ctx.TempUin, text)
#                 elif ctx.MsgType == MsgTypes.PhoneMsg:
#                     return await action.sendPhoneText(text)
#                 else:
#                     return await action.sendFriendText(ctx.FromUin, text)
#
#     async def aimage(
#         self, data: _T_Data, text: str = "", at: bool = False, type: int = 0
#     ):
#         """发送图片
#         :param data: 发送的内容, 可以为 路径字符串或路径Path对象， 可以为网络(URL)地址,
#         或者 base64 字符串, 或者为bytes(此时为base64)，或者为MD5或MD5列表，当为MD5列表(发送多图)时，参数text将无效
#
#         :param text: 图片附带的文字信息
#         :param at: 是否要艾特该用户
#         :param type: 发送内容的类型, 默认自动判断，可选值为 S.TYPE_?
#         """
#
#         if type not in (
#             TYPE_URL,
#             TYPE_MD5,
#             TYPE_BASE64,
#             TYPE_PATH,
#         ):
#             type, data = _resolve_data_type(data)
#
#         ctx = self.ctx
#         async with AsyncAction.from_ctx(ctx) as action:
#             if isinstance(ctx, GroupMsg):
#                 if at:
#                     text = macro.atUser(ctx.FromUserId) + text
#
#                 if type == TYPE_URL:
#                     return await action.sendGroupPic(ctx.FromGroupId, content=text, picUrl=data)  # type: ignore
#                 elif type == TYPE_BASE64:
#                     return await action.sendGroupPic(ctx.FromGroupId, content=text, picBase64Buf=data)  # type: ignore
#                 elif type == TYPE_MD5:
#                     return await action.sendGroupPic(
#                         ctx.FromGroupId, content=text, picMd5s=data  # type:ignore
#                     )
#                 elif type == TYPE_PATH:
#                     return await action.sendGroupPic(
#                         ctx.FromGroupId, content=text, picBase64Buf=file_to_base64(data)
#                     )
#             elif isinstance(ctx, FriendMsg):
#                 if ctx.TempUin:
#                     if type == TYPE_URL:
#                         return await action.sendPrivatePic(
#                             ctx.FromUin, ctx.TempUin, content=text, picUrl=data  # type: ignore
#                         )
#                     elif type == TYPE_BASE64:
#                         return await action.sendPrivatePic(
#                             ctx.FromUin, ctx.TempUin, content=text, picBase64Buf=data  # type: ignore
#                         )
#                     elif type == TYPE_MD5:
#                         return await action.sendPrivatePic(
#                             ctx.FromUin,
#                             ctx.TempUin,
#                             content=text,
#                             picMd5s=data,  # type:ignore
#                         )
#                     elif type == TYPE_PATH:
#                         return await action.sendPrivatePic(
#                             ctx.FromUin, ctx.TempUin, content=text, picBase64Buf=file_to_base64(data)  # type: ignore
#                         )
#                 else:
#                     if type == TYPE_URL:
#                         return await action.sendFriendPic(ctx.FromUin, content=text, picUrl=data)  # type: ignore
#                     elif type == TYPE_BASE64:
#                         return await action.sendFriendPic(ctx.FromUin, content=text, picBase64Buf=data)  # type: ignore
#                     elif type == TYPE_MD5:
#                         return await action.sendFriendPic(ctx.FromUin, content=text, picMd5s=data)  # type: ignore
#                     elif type == TYPE_PATH:
#                         return await action.sendFriendPic(ctx.FromUin, content=text, picBase64Buf=file_to_base64(data))  # type: ignore
#
#     async def avoice(self, data: _T_Data, type: int = 0):
#         """发送语音
#         :param data: 发送的内容, 可以为 路径字符串或路径Path对象， 可以为网络(URL)地址,
#         或者 base64 字符串, 或者为bytes(此时当作base64), 不支持MD5
#
#         :param type: 发送内容的类型, 默认自动判断，可选值为 S.TYPE_?
#         """
#
#         if type not in (
#             TYPE_URL,
#             TYPE_MD5,
#             TYPE_BASE64,
#             TYPE_PATH,
#         ):
#             type, data = _resolve_data_type(data)
#
#         assert type != TYPE_MD5, "语音不支持MD5发送"
#
#         ctx = self.ctx
#         async with AsyncAction.from_ctx(ctx) as action:
#             if isinstance(ctx, GroupMsg):
#                 if type == TYPE_URL:
#                     return await action.sendGroupVoice(ctx.FromGroupId, voiceUrl=data)  # type: ignore
#                 elif type == TYPE_BASE64:
#                     return await action.sendGroupVoice(ctx.FromGroupId, voiceBase64Buf=data)  # type: ignore
#                 elif type == TYPE_PATH:
#                     return await action.sendGroupVoice(ctx.FromGroupId, voiceBase64Buf=file_to_base64(data))  # type: ignore
#
#             elif isinstance(ctx, FriendMsg):
#                 if ctx.TempUin:
#                     if type == TYPE_URL:
#                         return await action.sendPrivateVoice(
#                             ctx.FromUin, ctx.TempUin, voiceUrl=data  # type: ignore
#                         )
#                     elif type == TYPE_BASE64:
#                         return await action.sendPrivateVoice(
#                             ctx.FromUin, ctx.TempUin, voiceBase64Buf=data  # type: ignore
#                         )
#                     elif type == TYPE_PATH:
#                         return await action.sendPrivateVoice(
#                             ctx.FromUin, ctx.TempUin, voiceBase64Buf=file_to_base64(data)  # type: ignore
#                         )
#                 else:
#                     if type == TYPE_URL:
#                         return await action.sendFriendVoice(ctx.FromUin, voiceUrl=data)  # type: ignore
#                     elif type == TYPE_BASE64:
#                         return await action.sendFriendVoice(ctx.FromUin, voiceBase64Buf=data)  # type: ignore
#                     elif type == TYPE_PATH:
#                         return await action.sendFriendVoice(ctx.FromUin, voiceBase64Buf=file_to_base64(data))  # type: ignore
#
#
S = _S()
