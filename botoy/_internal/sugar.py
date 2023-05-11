"""该模块封装发送操作

分三类场景：群消息、好友消息、私聊消息
"""
import asyncio
import base64
import functools
import re
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, List, Tuple, Union

from .action import Action
from .context import Context, current_ctx
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
    TYPE_AUTO = TYPE_AUTO
    TYPE_URL = TYPE_URL
    TYPE_BASE64 = TYPE_BASE64
    TYPE_MD5 = TYPE_MD5
    TYPE_PATH = TYPE_PATH

    # API必要参数
    _bot: int
    # 区分消息类型，选择发送目标
    _is_private: bool
    _group_id: int
    _user_id: int
    _user_name: str
    # 用于判断是否为框架默认对象
    _is_default: bool = True

    @classmethod
    def from_args(
        cls, bot: int, group_id: int, user_id: int, user_name: str, is_private: bool
    ):
        """给定S所需参数创建S
        API调用所需基本参数：``bot``
        剩余参数为发送目标判断参数:
            1. 所有消息都具有 ``user_id``, ``user_name``
            2. 群消息和私聊消息同时具有``group_id``, 所以使用额外标记``is_private``来区分群聊和私聊

        """
        s = cls()
        s._is_default = False
        s._bot = bot
        s._group_id = group_id
        s._user_id = user_id
        s._user_name = user_name
        s._is_private = is_private
        return s

    @classmethod
    def from_ctx(cls, ctx: Context):
        """从消息上下文ctx新建一个S，该方法从ctx中整理S所需参数。有关参数项请查看``from_args``方法注释获取详细说明"""
        s = cls()
        s._is_default = False
        if g := ctx.g:
            s._bot = g.bot_qq
            s._group_id = g.from_group
            s._user_id = g.from_user
            s._user_name = g.from_user_name
            s._is_private = False
        elif f := ctx.f:
            s._bot = f.bot_qq
            s._user_id = f.from_user
            s._user_name = f.from_user_name
            s._is_private = f.is_private
            s._group_id = f.from_group if f.is_private else 0
        return s

    def bind(self, ctx: Context) -> "_S":
        """新建一个绑定ctx的S"""
        return self.from_ctx(ctx)

    @property
    def _s(self):
        return _S.from_ctx(current_ctx.get()) if self._is_default else self

    async def text(self, text: str, at: bool = False):
        """发送文字
        :param text: 发送的文字内容
        :param at: 是否要艾特该用户
        """
        s = self._s
        async with Action(s._bot) as action:
            if s._is_private:
                return await action.sendPrivateText(s._user_id, s._group_id, text)
            else:
                if s._group_id:
                    return await action.sendGroupText(
                        s._group_id,
                        text,
                        s._user_id if at else 0,
                        s._user_name,
                    )
                else:
                    return await action.sendFriendText(s._user_id, text)

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

        s = self._s
        async with Action(s._bot) as action:
            if s._is_private:
                send = functools.partial(
                    action.sendPrivatePic, s._user_id, s._group_id, text=text
                )
            else:
                if s._group_id:
                    send = functools.partial(
                        action.sendGroupPic,
                        s._group_id,
                        text=text,
                        atUser=s._user_id if at else 0,
                        atUserNick=s._user_name if at else "",
                    )
                else:
                    send = functools.partial(
                        action.sendFriendPic, s._user_id, text=text
                    )

            if type == TYPE_URL:
                return await send(url=data)  # type: ignore
            elif type == TYPE_BASE64:
                return await send(base64=data)  # type: ignore
            elif type == TYPE_MD5:
                return await send(md5=data)  # type: ignore
            elif type == TYPE_PATH:
                return await send(base64=file_to_base64(data))  # type: ignore

    async def sleep(self, delay: float):
        """A shortcut of asyncio.sleep"""
        return await asyncio.sleep(delay)


S = _S()
