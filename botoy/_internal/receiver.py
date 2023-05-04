import asyncio
import inspect
import os
import re
import textwrap
import traceback
import weakref
from contextvars import ContextVar, copy_context
from pathlib import Path
from typing import Callable, Dict, List, NoReturn, Optional, Tuple, Union
from uuid import uuid4

from .context import Context as T_Context
from .context import FriendMsg as T_FriendMsg
from .context import GroupMsg as T_GroupMsg
from .context import current_ctx
from .keys import *
from .log import logger
from .sugar import _S as T_S
from .sugar import S

current_receiver: ContextVar["Receiver"] = ContextVar("current_receiver")


def start_session(
    group: Optional[bool] = None,
    friend: Optional[bool] = None,
    multi_user: Optional[bool] = None,
) -> "SessionExport":
    """开启会话

    由群消息开启会话
    ================

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
    """
    group = bool(group)
    friend = bool(friend)
    multi_user = bool(multi_user)
    ctx = current_ctx.get()
    if g := ctx.g:
        if g.is_from_self:
            raise RuntimeError("机器人本身无法创建会话, 请修正对话创建条件！")
        if group:
            if multi_user:
                friend = False
                sid = str(g.from_group)
            else:
                friend = True
                sid = f"{g.from_group}-{g.from_user}"
        elif friend:
            multi_user = False
            sid = str(g.from_user)
        else:
            group = True
            multi_user = False
            friend = True
            sid = f"{g.from_group}-{g.from_user}"
    elif f := ctx.f:
        if f.is_from_self:
            raise RuntimeError("机器人本身无法创建会话, 请修正对话创建条件！")
        group = multi_user = False
        sid = str(f.from_user)
    else:
        raise NotImplementedError("事件类型暂不支持创建对话")
    receiver = current_receiver.get()
    if sid in receiver.state:
        raise RuntimeError(f"该类型对话已经创建，不能重复创建。session id = {sid}")
    session = Session(sid, receiver, group, friend, multi_user)
    receiver.state[sid] = weakref.ref(session)
    logger.debug(f"{receiver=} start {session=}")
    return SessionExport(session)


class SessionExport:  # 避免代码补全太多不需要关注的内容
    def __init__(self, s: "Session") -> None:
        self.__s__ = s

    async def text(self, timeout=None):
        """获取下一条信息文本
        :param timeout: 超时时间，单位为秒。超时返回``None``。默认30s，可通过`set_default_timeout`修改。
        """
        return await self.__s__.next_text(timeout)

    async def must_text(self, timeout=None):
        """获取下一条信息文本
        :param timeout: 超时时间，单位为秒。超时直接结束对话。默认30s，可通过`set_default_timeout`修改。
        """
        text, s = await self.text(timeout)
        if text is None:
            self.finish()
        return text, s

    async def image(self, timeout=None):
        """获取下一条消息的图片内容(图片列表), 图片不可能为空
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        return await self.__s__.next_image(timeout)

    async def must_image(self, timeout=None):
        """获取下一条消息的图片内容(图片列表), 图片不可能为空
        :param timeout: 超时时间，单位为秒。超时直接结束会话。默认30s，可通过`set_default_timeout`修改。
        """
        images, s = await self.image(timeout)
        if images is None:
            self.finish()
        return images, s

    async def g(self, timeout=None):
        """获取下一条群消息
        如果该会话不支持捕捉群消息，将报错。超时返回``None``。默认30s，可通过`set_default_timeout`修改。
        """
        return await self.__s__.next_g(timeout)

    async def must_g(self, timeout=None):
        """获取下一条群消息
        如果该会话不支持捕捉群消息，将报错。超时直接结束对话。默认30s，可通过`set_default_timeout`修改。
        """
        msg, s = await self.g(timeout)
        if msg is None:
            self.finish()
        return msg, s

    async def f(self, timeout=None):
        """获取下一条好友消息
        如果该会话不支持捕捉好友消息，将报错。
        :param timeout: 超时时间，单位为秒。超时返回``None``。默认30s，可通过`set_default_timeout`修改。
        """
        return await self.__s__.next_f(timeout)

    async def must_f(self, timeout=None):
        """获取下一条好友消息
        如果该会话不支持捕捉好友消息，将报错。
        :param timeout: 超时时间，单位为秒。超时直接结束对话。默认30s，可通过`set_default_timeout`修改。
        """
        msg, s = await self.f(timeout)
        if msg is None:
            self.finish()
        return msg, s

    async def ctx(self, timeout=None):
        """获取下一个ctx
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        return await self.__s__.next_ctx(timeout)

    async def must_ctx(self, timeout=None):
        """获取下一个ctx
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        c, s = await self.ctx(timeout)
        if c is None:
            self.finish()
        return c, s

    def set_default_timeout(self, timeout: int):
        """设置消息等待的默认超时时间，单位为秒
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        self.__s__.set_default_timeout(timeout)

    def finish(self, info: str = "") -> NoReturn:
        """结束会话"""
        return self.__s__.finish(info)

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
        group: bool,
        friend: bool,
        multi_user: bool,
    ):
        self.sid = sid
        self.receiver = receiver
        self.queue = asyncio.Queue[T_Context]()
        self.lock = asyncio.Lock()
        self.default_timeout = 30

        self.group = bool(group)
        self.friend = bool(friend)
        self.multi_user = bool(multi_user)

        self._waiting_group = False
        self._waiting_friend = False

        self.finished = False  # py没法做到理想raii， 加个标记吧

        self.prev_s: Optional[T_S] = None

    def finish(self, info: str = "") -> NoReturn:
        self.finished = True
        if info:
            raise FinishSession({"info": info, "s": self.prev_s or S})
        else:
            raise FinishSession

    def set_default_timeout(self, timeout: int):
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

    async def get_ctx(self, timeout=None) -> Optional[T_Context]:
        """队列中获取ctx
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        try:
            return await asyncio.wait_for(
                self.queue.get(), timeout or self.default_timeout
            )
        except asyncio.TimeoutError:
            return None

    async def next_text(self, timeout=None) -> Tuple[Optional[str], T_S]:
        """获取下一条消息的文本内容
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        the_ctx, the_S = await self.next_ctx(timeout=timeout)
        if the_ctx and the_S:
            if msg := the_ctx.f or the_ctx.g:  # 在receiver里进行了消息过滤, 此处无需再次判断
                return msg.text, the_S
        return None, the_S

    async def next_image(self, timeout=None):
        """获取下一条消息的图片内容(图片列表), 图片不可能为空
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        the_ctx, the_S = await self.next_ctx(timeout=timeout)
        if the_ctx and the_S:
            if msg := the_ctx.f or the_ctx.g:
                if msg.images:
                    return msg.images, the_S
        return None, the_S

    async def next_g(self, timeout=None) -> Tuple[Optional[T_GroupMsg], T_S]:
        """获取下一条群消息
        如果该会话不支持捕捉群消息，将报错。
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        if not self.allow_waiting_group:
            raise RuntimeError("该会话不支持获取群消息")
        async with self.lock:
            self._waiting_group = True
        the_ctx = await self.get_ctx(timeout)
        async with self.lock:
            self._waiting_group = False
        if the_ctx:
            self.prev_s = S.bind(the_ctx)
            return the_ctx.g, self.prev_s
        return None, S

    async def next_f(self, timeout=None) -> Tuple[Optional[T_FriendMsg], T_S]:
        """获取下一条好友消息
        如果该会话不支持捕捉好友消息，将报错。
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
        if not self.allow_waiting_group:
            raise RuntimeError("该会话不支持获取好友消息")
        async with self.lock:
            self._waiting_friend = True
        the_ctx = await self.get_ctx(timeout)
        async with self.lock:
            self._waiting_friend = False
        if the_ctx:
            self.prev_s = S.bind(the_ctx)
            return the_ctx.f, self.prev_s
        return None, S

    async def next_ctx(self, timeout=None) -> Tuple[Optional[T_Context], T_S]:
        """获取下一个ctx
        :param timeout: 超时时间，单位为秒。超时返回`None`。默认30s，可通过`set_default_timeout`修改。
        """
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
        return None, S

    def __repr__(self) -> str:
        return f"<Session[sid={self.sid}]>"


class ReceiverMarker:
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

        receiver.__dict__[RECEIVER_INFO] = ReceiverInfo(
            **{
                "author": author or "",
                "usage": usage or receiver.__doc__ or "",
                "name": name or receiver.__name__.strip("r_") or "",  # 注意r_
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
        self.name = kwargs.get("name", "")
        self.author = kwargs.get("author", "")
        self.usage = kwargs.get("usage", "")
        self.meta = kwargs.get("meta", "")

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
                            if session.waiting:
                                await session.add_ctx(ctx)
                        else:
                            del self.state[sid]
                        return
            elif f := ctx.f:
                this_user = f.from_user
                for sid, session_ref in self.state.items():
                    if this_user == int(sid.split("-")[-1]):
                        if session := session_ref():
                            if session.waiting:
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
