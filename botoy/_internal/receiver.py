import asyncio
import inspect
import os
import random
import re
import string
import textwrap
import traceback
import weakref
from contextvars import ContextVar, copy_context
from pathlib import Path
from typing import Any, Callable, Dict, List, NoReturn, Optional, Tuple, TypeVar, Union
from uuid import uuid4

from .context import Context as T_Context
from .context import FriendMsg as T_FriendMsg
from .context import GroupMsg as T_GroupMsg
from .context import current_ctx
from .keys import *
from .log import logger
from .sugar import _S as T_S
from .sugar import S

T = TypeVar("T")

current_receiver: ContextVar["Receiver"] = ContextVar("current_receiver")


def start_session(
    group: Optional[Union[bool, int]] = None,
    friend: Optional[Union[bool, int]] = None,
    multi_user: Optional[bool] = None,
    skip_responder: bool = True,
) -> "SessionExport":
    """开启会话

    约定：只分群消息和好友消息，好友消息与私聊消息在本节所表示含义一致。

    Args: group friend multi_user

    >>> 参数group和friend都不是整数类型的情况 <<<

    由群消息开启会话
    ================

    -

    A. ``group=True``, ``friend``参数失效

    - ``multi_user=True``
        会话为该群所有用户共享。该群所有消息都会被捕获。``session``无法获取下一条好友消息（无法调用``f``方法，并且``ctx``方法只返回群消息）

    - ``multi_user=False``
        会话为该群该用户共享，同时自动支持好友消息。来自该用户在该群的消息以及该用户的私聊消息都会被捕获。

    B. ``friend=True``

    开启与该用户的私聊会话。只捕获该用户的私聊消息。

    C. 默认行为

    会话为该群该用户共享，同时自动支持好友消息。来自该用户在该群的消息以及该用户的私聊消息都会被捕获。


    由私聊消息开启会话
    ==================

    固定一种行为（参数全部无效）。开启与该用户的私聊会话。只捕获该用户的私聊消息。


    由事件消息开启会话
    ==================

    暂不支持

    参数处理或组合的优先级为：group > multi_user > friend
    -

    >>> 参数group和friend存在整数类型的情况 <<<

    直接传入群ID，用户ID来开启指定对话

    - 仅指定群id(group)时：参数friend和multi_user均被忽略。此时捕获指定群所有消息。

    - 仅指定用户id(friend)时：参数group和multi_user均被忽略。此时仅捕获指定用户私聊消息。

    - 同时指定群id(group)和用户id(friend)时：

      如果开启多用户(multi_user)，将忽略参数friend。此时捕获指定群所有消息。
      如果关闭多用户(multi_user)，此时捕获该群来自该用户在该群的消息以及该用户的私聊消息。

    参数处理或组合的优先级为：group > multi_user > friend
    -

    Args: skip_responder
    -

    参数``skip_responder``表示跳过抢答。在处在对话中，程序还在处理其他逻辑，此时并不需要用户的输入，但用户仍然可能发送信息，比如用户对当前功能十分熟悉。
    该行为被定义为抢答。
    当该参数为``True``时，仅当``正在``请求用户消息时才会处理新消息。
    当该参数为``False``时，用户消息会被存入队列，当请求用户消息时，会直接作为最新消息返回。
    """
    # prepare
    group = bool(group) if group is None else group
    friend = bool(friend) if friend is None else friend
    multi_user = bool(multi_user)
    ctx = current_ctx.get()
    # logic
    group_int = not isinstance(group, bool)  # bool is int, int is not bool...
    friend_int = not isinstance(friend, bool)
    if group_int or friend_int:
        if group_int:
            if multi_user:
                friend = False
                sid = str(group)
                # 群, 不绑定人
                s = S.from_args(ctx.bot_qq, group, 0, "", False)
            else:
                if friend_int:
                    sid = f"{group}-{friend}"
                    # 私聊
                    s = S.from_args(ctx.bot_qq, group, friend, "", True)
                else:
                    friend = False
                    multi_user = True
                    sid = str(group)
                    # 群, 不绑定人
                    s = S.from_args(ctx.bot_qq, group, 0, "", False)
        else:
            multi_user = False
            group = False
            sid = str(friend)
            # 私聊（好友）
            s = S.from_args(ctx.bot_qq, 0, friend, "", False)

    else:
        if g := ctx.g:
            if g.is_from_self:
                raise RuntimeError("机器人本身无法创建会话, 请修正对话创建条件！")
            if group:
                if multi_user:
                    friend = False
                    sid = str(g.from_group)
                    s = S.from_ctx(ctx)
                else:
                    friend = True
                    sid = f"{g.from_group}-{g.from_user}"
                    s = S.from_ctx(ctx)
            elif friend:
                multi_user = False
                sid = str(g.from_user)
                # 私聊
                s = S.from_args(
                    ctx.bot_qq, g.from_group, g.from_user, g.from_user_name, True
                )
            else:
                group = True
                multi_user = False
                friend = True
                sid = f"{g.from_group}-{g.from_user}"
                s = S.from_ctx(ctx)
        elif f := ctx.f:
            if f.is_from_self:
                raise RuntimeError("机器人本身无法创建会话, 请修正对话创建条件！")
            group = multi_user = False
            sid = str(f.from_user)
            s = S.from_ctx(ctx)
        else:
            raise NotImplementedError("事件类型暂不支持创建对话")
    receiver = current_receiver.get()
    if sid in receiver.state:
        raise RuntimeError(f"该类型对话已经创建，不能重复创建。session id = {sid}")
    session = Session(sid, receiver, group, friend, multi_user, skip_responder)
    session.set_s(s)
    receiver.state[sid] = weakref.ref(session)
    logger.debug(f"{receiver=} start {session=}")
    return SessionExport(session)


class SessionExport:  # 避免代码补全太多不需要关注的内容, 同时也用于添加额外功能
    def __init__(self, s: "Session") -> None:
        self.__s__ = s

    async def text(self, info: str = "", timeout: Optional[float] = None):
        """获取下一条信息文本
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时返回``None``。默认30s，可通过`set_default_timeout`修改。
        """
        return await self.__s__.next_text(info, timeout)

    async def must_text(self, info: str = "", timeout: Optional[float] = None):
        """获取下一条信息文本
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时直接结束对话。默认30s，可通过`set_default_timeout`修改。
        """
        text, s = await self.text(info, timeout)
        if text is None:
            self.finish()
        return text, s

    async def image(self, info: str = "", timeout: Optional[float] = None):
        """获取下一条消息的图片内容(图片列表), 图片不可能为空
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        return await self.__s__.next_image(info, timeout)

    async def must_image(self, info: str = "", timeout: Optional[float] = None):
        """获取下一条消息的图片内容(图片列表), 图片不可能为空
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时直接结束会话。默认30s，可通过`set_default_timeout`修改。
        """
        images, s = await self.image(info, timeout)
        if images is None:
            self.finish()
        return images, s

    async def g(self, info: str = "", timeout: Optional[float] = None):
        """获取下一条群消息
        如果该会话不支持捕捉群消息，将报错。超时返回``None``。默认30s，可通过`set_default_timeout`修改。
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时返回``None``。默认30s，可通过`set_default_timeout`修改。
        """
        return await self.__s__.next_g(info, timeout)

    async def must_g(self, info: str = "", timeout: Optional[float] = None):
        """获取下一条群消息
        如果该会话不支持捕捉群消息，将报错。超时直接结束对话。默认30s，可通过`set_default_timeout`修改。
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时返回``None``。默认30s，可通过`set_default_timeout`修改。
        """
        msg, s = await self.g(info, timeout)
        if msg is None:
            self.finish()
        return msg, s

    async def f(self, info: str = "", timeout: Optional[float] = None):
        """获取下一条好友消息
        如果该会话不支持捕捉好友消息，将报错。
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时返回``None``。默认30s，可通过`set_default_timeout`修改。
        """
        return await self.__s__.next_f(info, timeout)

    async def must_f(self, info: str = "", timeout: Optional[float] = None):
        """获取下一条好友消息
        如果该会话不支持捕捉好友消息，将报错。
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时直接结束对话。默认30s，可通过`set_default_timeout`修改。
        """
        msg, s = await self.f(info, timeout)
        if msg is None:
            self.finish()
        return msg, s

    async def ctx(self, info: str = "", timeout: Optional[float] = None):
        """获取下一个ctx
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        return await self.__s__.next_ctx(info, timeout)

    async def must_ctx(self, info: str = "", timeout: Optional[float] = None):
        """获取下一个ctx
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        c, s = await self.ctx(info, timeout)
        if c is None:
            self.finish()
        return c, s

    async def confirm(
        self,
        text: str,
        default: bool = False,
        timeout: Optional[float] = None,
        show_default: bool = True,
    ) -> bool:
        """提示确认消息
        该方法会一直询问用户确认，直到超时或者用户输入正确 y 表示 yes, n 表示 no, 输入不区分大小写
        :param text: 需要确认的问题
        :param default: 如果回复超时则返回该默认值
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        :param show_default: 在问题后显示超时默认值
        """
        timeout = timeout or self.__s__.default_timeout
        if show_default:
            prompt = f"[y/N] {timeout}秒超时，默认为{default and 'yes' or 'no'}"
        else:
            prompt = f"[y/N] {timeout}秒超时"
        user_text, _ = await self.text(f"{text}\n\n{prompt}", timeout)
        while True:
            if user_text is None:
                return default
            elif user_text.lower() == "y":
                return True
            elif user_text.lower() == "n":
                return False
            else:
                user_text, _ = await self.text(f"无效输入\n\n{text}\n\n{prompt}")

    async def select(
        self,
        candidates: List[T],
        prompt: str = "",
        retry_times: int = 1,
        key: Optional[Callable[[T], Any]] = None,
        always_prompt: bool = True,
        timeout: Optional[float] = None,
    ) -> Optional[Tuple[T, int]]:
        """提示用户发送序号选择列表中的一项,
        返回值为元组: (选择项, 对应索引)。 超出重试次数或超时，返回None

        :param candidates: 选项列表
        :param prompt: 提示信息, 一般可设置为当前操作的标题
        :param retry_times: 重试次数
        :param key: 一个函数，参数为候选列表中项，返回的值将用于作为选项的标签, 默认为`str`函数
        :param always_prompt: 重试时是否再次发送提示
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        key = key or str
        timeout = timeout or self.__s__.default_timeout
        items = list(key(candidate) for candidate in candidates)
        info = "\n".join([f"【{idx}】 {item}" for idx, item in enumerate(items, 1)])

        ret, s = await self.text(
            f"{prompt}\n发送序号选择一项(总次数：{retry_times}次, 超时时间：{timeout}秒)" + "\n" + info,
            timeout,
        )
        while retry_times > 0:
            retry_times -= 1
            if ret is None:
                return
            try:
                idx = int(ret) - 1
                return candidates[idx], idx
            except Exception:
                pass
            if retry_times > 0:
                msg = (
                    f"{prompt}\n序号错误。\n发送序号选择一项(剩余次数：{retry_times}次, 超时时间：{timeout}秒)"
                    + (f"\n{info}" if always_prompt else "")
                )
                ret, s = await self.text(msg, timeout)
            else:
                await s.text("{prompt}\n序号错误，已退出选择。")
        return

    def set_default_timeout(self, timeout: float):
        """设置消息等待的默认超时时间，单位为秒
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        self.__s__.set_default_timeout(timeout)

    def finish(self, info: str = "") -> NoReturn:
        """结束会话
        :param info: 可选提示信息
        """
        return self.__s__.finish(info)

    def set_finish_info(self, info: Union[Callable[[], str], str]):
        """设置finish时的默认提示信息，默认为空不发送。
        :param info: 可以是字符串或者返回字符串的函数
        """
        return self.__s__.set_finish_info(info)

    def __repr__(self) -> str:
        return self.__s__.__repr__()

    def __del__(self):
        del self.__s__


class FinishSession(Exception):
    """抛异常快速跳出执行"""


class Session:
    def __init__(
        self,
        sid: str,
        receiver: "Receiver",
        group: Union[bool, int],
        friend: Union[bool, int],
        multi_user: bool,
        skip_responder: bool,
    ):
        self.sid = sid
        self.receiver = receiver
        self.queue = asyncio.Queue[T_Context]()
        self.lock = asyncio.Lock()
        self.default_timeout = 30

        self.group = group
        self.friend = friend
        self.multi_user = multi_user
        self.skip_responder = skip_responder

        self._waiting_group = False
        self._waiting_friend = False

        self.finished = False  # py没法做到理想raii， 加个标记吧

        self.prev_s: Optional[T_S] = None

        # 调用finish的默认提示信息，字符串或者返回字符串的函数
        self.finish_info: Union[Callable[[], str], str] = ""

    def set_s(self, s):
        self.prev_s = s

    def set_finish_info(self, info: Union[Callable[[], str], str]):
        """设置finish时的默认提示信息，默认为空不发送。
        :param info: 可以是字符串或者返回字符串的函数
        """
        self.finish_info = info

    def finish(self, info: str = "") -> NoReturn:
        """可选提示结束信息"""
        if not info and self.finish_info:
            if isinstance(self.finish_info, str):
                info = self.finish_info
            else:
                info = self.finish_info()
        self.finished = True
        if info:
            raise FinishSession({"info": info, "s": self.prev_s or S})
        else:
            raise FinishSession

    def set_default_timeout(self, timeout: float):
        """设置消息等待的默认超时时间, 默认30s，单位为秒"""
        self.default_timeout = timeout

    @property
    def allow_waiting_group(self):
        return self.group

    @property
    def allow_waiting_friend(self):
        return self.friend

    @property
    def waiting(self):
        return self._waiting_group or self._waiting_friend

    @property
    def waiting_group(self):
        return self._waiting_group

    @property
    def waiting_friend(self):
        return self._waiting_friend

    async def add_ctx(self, ctx: T_Context):
        async with self.lock:
            if (self.waiting_friend and ctx.f) or (self.waiting_group and ctx.g):
                await self.queue.put(ctx)
                self._waiting_friend = self._waiting_group = False

    async def get_ctx(self, timeout: Optional[float] = None) -> Optional[T_Context]:
        """队列中获取ctx
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        try:
            return await asyncio.wait_for(
                self.queue.get(), timeout or self.default_timeout
            )
        except asyncio.TimeoutError:
            return None

    async def next_text(
        self, info: str = "", timeout: Optional[float] = None
    ) -> Tuple[Optional[str], T_S]:
        """获取下一条消息的文本内容
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        if info:
            await (self.prev_s or S).text(info)
        the_ctx, the_S = await self.next_ctx(timeout=timeout)
        if the_ctx and the_S:
            if msg := the_ctx.f or the_ctx.g:  # 在receiver里进行了消息过滤, 此处无需再次判断
                return msg.text, the_S
        return None, the_S

    async def next_image(self, info: str = "", timeout: Optional[float] = None):
        """获取下一条消息的图片内容(图片列表), 图片不可能为空
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        if info:
            await (self.prev_s or S).text(info)
        the_ctx, the_S = await self.next_ctx(timeout=timeout)
        if the_ctx and the_S:
            if msg := the_ctx.f or the_ctx.g:
                if msg.images:
                    return msg.images, the_S
        return None, the_S

    async def next_g(
        self, info: str = "", timeout: Optional[float] = None
    ) -> Tuple[Optional[T_GroupMsg], T_S]:
        """获取下一条群消息
        如果该会话不支持捕捉群消息，将报错。
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        if not self.allow_waiting_group:
            raise RuntimeError("该会话不支持获取群消息")
        if info:
            await (self.prev_s or S).text(info)
        async with self.lock:
            self._waiting_group = True
        the_ctx = await self.get_ctx(timeout)
        async with self.lock:
            self._waiting_group = False
        if the_ctx:
            self.prev_s = S.bind(the_ctx)
            return the_ctx.g, self.prev_s
        return None, self.prev_s or S

    async def next_f(
        self, info: str = "", timeout: Optional[float] = None
    ) -> Tuple[Optional[T_FriendMsg], T_S]:
        """获取下一条好友消息
        如果该会话不支持捕捉好友消息，将报错。
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        if not self.allow_waiting_group:
            raise RuntimeError("该会话不支持获取好友消息")
        if info:
            await (self.prev_s or S).text(info)
        async with self.lock:
            self._waiting_friend = True
        the_ctx = await self.get_ctx(timeout)
        async with self.lock:
            self._waiting_friend = False
        if the_ctx:
            self.prev_s = S.bind(the_ctx)
            return the_ctx.f, self.prev_s
        return None, self.prev_s or S

    async def next_ctx(
        self, info: str = "", timeout: Optional[float] = None
    ) -> Tuple[Optional[T_Context], T_S]:
        """获取下一个ctx
        :param info: 可选的提示信息
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        if info:
            await (self.prev_s or S).text(info)
        async with self.lock:
            self._waiting_group = True
            self._waiting_friend = True
        the_ctx = await self.get_ctx(timeout or self.default_timeout)
        async with self.lock:
            self._waiting_group = False
            self._waiting_friend = False
        if the_ctx:
            self.prev_s = S.bind(the_ctx)
            return the_ctx, self.prev_s
        return None, self.prev_s or S

    def __repr__(self) -> str:
        return f"<Session[sid={self.sid}]>"


class ReceiverMarker:
    def __init__(self) -> None:
        self.__name_codes = []

    def __gen_naming_code(self) -> str:
        chars = list(string.ascii_lowercase)
        code = "".join(random.choices(chars, k=3))
        while code in self.__name_codes:
            code = "".join(random.choices(chars, k=3))
        self.__name_codes.append(code)
        return code

    def __call__(
        self,
        receiver,
        name="",
        author="",
        usage="",
        *,
        _directly_attached=False,
        _back=1,
    ):
        """标记接收函数
        :param receiver: 接收函数
        :param name: 插件名称，默认为__name__
        :param author: 插件作者，默认为空
        :param usage: 插件用法，默认为__doc__

        TODO: 目前信息仅用在加载打印插件信息，后续可进行应用
        """
        receiver.__dict__[IS_RECEIVER] = True
        meta = ""
        if file := inspect.getsourcefile(receiver):
            meta += str(Path(file).relative_to(os.getcwd()))
        try:
            lines = inspect.getsourcelines(receiver)
            if meta:
                meta += " line {}".format(lines[1])
        except:
            pass

        code = self.__gen_naming_code()
        name = name or receiver.__name__.strip("r_") or ""
        name = f"{name} {code}" if name else code
        receiver.__dict__[RECEIVER_INFO] = ReceiverInfo(
            **{
                "author": author or "",
                "usage": usage or receiver.__doc__ or "",
                "name": name,
                "meta": meta or "",
            }
        )

        # 插件通过加入额外信息标记接收函数, 其前提该函数能在import后的module中`被检索`到
        # 被attach调用时，函数会被直接添加，所以无需进行该操作
        if not _directly_attached:
            frame = inspect.currentframe()
            for _ in range(_back):
                frame = frame.f_back  # type: ignore
            _globals = frame.f_globals  # type: ignore
            if receiver not in _globals.values():
                u = "receiver" + str(uuid4())
                _globals[u] = receiver
        return self

    def __add__(self, receiver: Union[Callable, Tuple, List]):
        if receiver == self:
            pass
        elif callable(receiver):
            self(receiver, _back=2)
        elif isinstance(receiver, (List, Tuple)):
            items = list(receiver)
            items.extend(["", "", ""])
            self(items[0], *items[1:3], _back=2)
        else:
            # TODO ???
            pass
        return self


mark_recv = ReceiverMarker()


def is_recv(receiver):
    try:
        return receiver.__dict__.get(IS_RECEIVER, False)
    except Exception:
        return False


class ReceiverInfo:
    def __init__(self, **kwargs):
        self.name: str = kwargs.get("name", "")
        self.author: str = kwargs.get("author", "")
        self.usage: str = kwargs.get("usage", "")
        self.meta: str = kwargs.get("meta", "")

    def __repr__(self) -> str:
        return f"<ReceiverInfo[{self.name}]>"


class Receiver:
    def __init__(self, callback: Callable, info=None, pool=None):
        self.callback = callback
        self.pool = pool
        self.info = info or ReceiverInfo()
        self.last_execution = None
        # 存储session
        # 1. groupID 该群所有人, 不包括私聊
        # 2. groupID-userID 该群对应用户, 包括私聊
        # 3. userID 仅该用户私聊
        self.state: Dict[str, weakref.ReferenceType[Session]] = {}

        # 没检测出问题也不大
        source = inspect.getsource(callback)
        self.using_session = bool(re.findall(r"start_session\(.*?\)", source))
        if self.using_session:
            logger.debug(f"using session => {self}")

    async def __call__(self):
        current_receiver.set(self)

        ctx = current_ctx.get()

        # clean
        for k, v in self.state.items():
            _s = v()
            if _s is None or _s.finished:
                del self.state[k]

        if not self.state:
            if self.using_session and self.last_execution:
                try:
                    # 给一定的时间用于用户确定是否开启会话的逻辑
                    await asyncio.wait_for(self.last_execution, 2)
                except asyncio.TimeoutError:
                    pass

        if self.state:
            logger.debug(f"{self} => state={self.state}")
            if g := ctx.g:
                this_group, this_user = g.from_group, g.from_user
                for sid in (f"{this_group}-{this_user}", str(this_group)):
                    if session_ref := self.state.get(sid):
                        if session := session_ref():
                            if session.waiting or not session.skip_responder:
                                await session.add_ctx(ctx)
                        else:
                            del self.state[sid]
                        return
            elif f := ctx.f:
                this_user = f.from_user
                for sid, session_ref in self.state.items():
                    if this_user == int(sid.split("-")[-1]):
                        if session := session_ref():
                            if session.waiting or not session.skip_responder:
                                await session.add_ctx(ctx)
                        else:
                            del self.state[sid]
                        return

        try:
            if asyncio.iscoroutinefunction(self.callback):
                self.last_execution = asyncio.ensure_future(self.callback())
            else:
                all_ctx = copy_context()
                self.last_execution = asyncio.get_running_loop().run_in_executor(
                    self.pool, lambda: all_ctx.run(self.callback)
                )
            await self.last_execution
        except asyncio.CancelledError:
            pass
        except FinishSession as e:
            if e.args and (arg := e.args[0]):
                await arg["s"].text(arg["info"])
        except Exception:
            logger.error(
                "Error occured in receiver：\n"
                + textwrap.indent(traceback.format_exc(), " " * 2)
            )

    def __repr__(self) -> str:
        return f"<Receiver[{self.info}]>"
