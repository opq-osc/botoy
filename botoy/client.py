# pylint: disable = too-many-instance-attributes, W0212
import asyncio
import copy
import functools
import inspect
import random
import time
from collections.abc import Sequence
from typing import Callable, List, Optional, Tuple, Union

import socketio
from socketio.exceptions import ConnectionError as SioConnectionError

from .config import jconfig
from .log import logger, logger_init
from .model import EventMsg, FriendMsg, GroupMsg
from .plugin import PluginManager
from .pool import WorkerPool
from .typing import (
    T_EventMiddleware,
    T_EventReceiver,
    T_FriendMsgMiddleware,
    T_FriendMsgReceiver,
    T_GeneralReceiver,
    T_GroupMsgMiddleware,
    T_GroupMsgReceiver,
)
from .utils import check_schema, sync_run, to_address

#######################
#     socketio
#        | dict
#  message handler
#        | context
#  context middleware
#        | new context
#     receiver
#######################


class Botoy:
    """
    :param qq: 机器人QQ号(多Q就传qq号列表), 如果不传则会监听服务端传过来的所有机器人的
                所有信息，如果传了，则只会接收对应机器人的信息. 0会被忽略，相当于没传
    :param use_plugins: 是否开启插件功能, 默认``False``
    :param port: 运行端口, 默认为``8888``
    :param host: ip，默认为``http://127.0.0.1``
    :param group_blacklist: 群黑名单, 此名单中的群聊消息不会被处理,默认为``空``
    :param friend_blacklist: 好友黑名单，此名单中的好友消息不会被处理，默认为``空``
    :param blocked_users: 用户黑名单，即包括群消息和好友消息, 该用户的消息都不会处理, 默认为``空``
    :param log: 该参数控制控制台日志等级,为True输出INFO等级日志,为False输出EROOR等级的日志
    :param log_file: 该参数控制日志文件开与关,为True输出INFO等级日志的文件,为False关闭输出日志文件
    """

    # 主要为了重载功能，因为重载不需要用到bot的功能
    # 如果在初始化实例时就导入插件, 导入插件会多执行一次插件,
    # 在初次访问时初始化更符合常理，也防止了部分潜在bug
    class LazyPluginManager:
        def __get__(self, obj, _):
            mgr = PluginManager()
            if obj.use_plugins:
                mgr.load_plugins()
                print(mgr.info)
            value = obj.__dict__["plugMgr"] = mgr
            return value

    plugMgr: PluginManager = LazyPluginManager()  # type: ignore

    def __init__(
        self,
        *,
        qq: Optional[Union[int, List[int]]] = None,
        use_plugins: Optional[bool] = False,
        port: Optional[int] = None,
        host: Optional[str] = None,
        group_blacklist: Optional[List[int]] = None,
        friend_blacklist: Optional[List[int]] = None,
        blocked_users: Optional[List[int]] = None,
        log: bool = True,
        log_file: bool = False,
    ):
        if qq is not None:
            if not isinstance(qq, str) and isinstance(qq, Sequence):
                self.qq = list(qq)
            else:
                self.qq = [qq]  # type: ignore
        else:
            self.qq = []
        self.qq: List[int] = [int(qq) for qq in self.qq if int(qq) != 0]

        self.host = check_schema(host or jconfig.host)
        self.port = int(port or jconfig.port)
        self.address = to_address(self.host, self.port)
        self.group_blacklist = group_blacklist or jconfig.group_blacklist
        self.friend_blacklist = friend_blacklist or jconfig.friend_blacklist
        self.blocked_users = blocked_users or jconfig.blocked_users
        self.webhook = jconfig.webhook

        # 日志
        logger_init(log, log_file)

        # 调用close方法需要调用的函数，每个接收一个参数 wait
        self._close_callbacks = []

        # 消息接收函数列表
        # 这里只储存主体文件中通过装饰器或函数添加的接收函数
        self._friend_msg_receivers: List[T_FriendMsgReceiver] = []
        self._group_msg_receivers: List[T_GroupMsgReceiver] = []
        self._event_receivers: List[T_EventReceiver] = []

        # 消息上下文对象中间件列表
        # 中间件以对应消息上下文为唯一参数，返回值与上下文类型一致则向下传递
        # 否则直接丢弃该次消息
        self._friend_context_middlewares: List[T_FriendMsgMiddleware] = []
        self._group_context_middlewares: List[T_GroupMsgMiddleware] = []
        self._event_context_middlewares: List[T_EventMiddleware] = []

        # webhook
        if self.webhook:
            from . import webhook  # pylint: disable=C0415

            flag = self.__class__.__name__.startswith("Async") and "async_" or ""

            self._friend_msg_receivers.append(getattr(webhook, f"{flag}friend"))
            self._group_msg_receivers.append(getattr(webhook, f"{flag}group"))
            self._event_receivers.append(getattr(webhook, f"{flag}event"))

        # 插件管理
        # 管理插件提供的接收函数
        self.use_plugins = use_plugins

        # 当连接上或断开连接运行的函数
        # 如果通过装饰器注册了, 这两个字段设置成(func, every_time)
        # func 是需要执行的函数， every_time 表示是否每一次连接或断开都会执行
        self._when_connected_do: Optional[Tuple[Callable, bool]] = None
        self._when_disconnected_do: Optional[Tuple[Callable, bool]] = None

        # 线程池 TODO: 开放该参数
        thread_works = 50
        self._pool = WorkerPool(thread_works)
        self._close_callbacks.append(self._pool.shutdown)

        # 初始化消息包接收函数
        self._friend_msg_handler = self._msg_handler_factory(FriendMsg)
        self._group_msg_handler = self._msg_handler_factory(GroupMsg)
        self._event_handler = self._msg_handler_factory(EventMsg)

    ########################################################################
    # message handler
    ########################################################################
    def _msg_handler_factory(self, cls):
        def handler(msg):
            return self._context_handler(cls(msg))

        return handler

    def _context_handler(self, context: Union[FriendMsg, GroupMsg, EventMsg]):
        passed_context = self._context_checker(context)
        if passed_context:
            return self._pool.submit(self._context_distributor, context)
        return

    def _context_checker(self, context: Union[FriendMsg, GroupMsg, EventMsg]):
        if self.qq and context.CurrentQQ not in self.qq:
            return

        logger.info(f"{context.__class__.__name__} ->  {context.data}")

        if isinstance(context, FriendMsg):
            if context.FromUin in (
                *self.friend_blacklist,
                *self.blocked_users,
            ):
                return
            middlewares = self._friend_context_middlewares

        elif isinstance(context, GroupMsg):
            if (
                context.FromGroupId in self.group_blacklist
                or context.FromUserId in self.blocked_users
            ):
                return
            middlewares = self._group_context_middlewares

        else:
            middlewares = self._event_context_middlewares

        context_type = type(context)
        for middleware in middlewares:
            new_context = middleware(context)  # type: ignore
            if not (new_context and isinstance(new_context, context_type)):
                return
            context = new_context

        setattr(context, "_host", self.host)
        setattr(context, "_port", self.port)

        return context

    ########################################################################
    # context distributor
    ########################################################################
    def _context_distributor(self, context: Union[FriendMsg, GroupMsg, EventMsg]):
        for receiver in self._get_context_receivers(context):
            new_context = copy.deepcopy(context)
            if asyncio.iscoroutinefunction(receiver):
                self._pool.submit(sync_run, receiver(new_context))  # type: ignore
            else:
                self._pool.submit(receiver, new_context)

    def _get_context_receivers(self, context: Union[FriendMsg, GroupMsg, EventMsg]):

        if isinstance(context, FriendMsg):
            receivers = [
                *self._friend_msg_receivers,
                *self.plugMgr.friend_msg_receivers,
            ]
        elif isinstance(context, GroupMsg):
            receivers = [
                *self._group_msg_receivers,
                *self.plugMgr.group_msg_receivers,
            ]
        else:
            receivers = [
                *self._event_receivers,
                *self.plugMgr.event_receivers,
            ]

        return receivers

    ########################################################################
    # Add context receivers
    ########################################################################
    def on(self, receiver: T_GeneralReceiver):
        """添加通用接收函数"""
        signature = inspect.signature(receiver)
        parameters = list(signature.parameters.values())
        ctx = parameters[0]
        annotation = ctx.annotation

        is_friend = False
        is_group = False
        is_event = False
        # 1. 未指定类型，全部接收
        if annotation == inspect._empty:
            is_friend = is_group = is_event = True
        # 2. 单个类型
        elif annotation in ("FriendMsg", FriendMsg):
            is_friend = True
        elif annotation in ("GroupMsg", GroupMsg):
            is_group = True
        elif annotation in ("EventMsg", EventMsg):
            is_event = True
        # 3. 联合类型
        else:
            args = annotation.__args__
            is_friend = FriendMsg in args
            is_group = GroupMsg in args
            is_event = EventMsg in args

        if is_friend:
            self._friend_msg_receivers.append(receiver)  # type: ignore
        if is_group:
            self._group_msg_receivers.append(receiver)  # type: ignore
        if is_event:
            self._event_receivers.append(receiver)  # type: ignore

        return self

    def on_friend_msg(self, receiver: T_FriendMsgReceiver):
        """添加好友消息接收函数"""
        self._friend_msg_receivers.append(receiver)
        return self  # 包括下面的六个方法是都不需要返回值的, 但返回本身也无妨,可以支持链式初始化

    def on_group_msg(self, receiver: T_GroupMsgReceiver):
        """添加群消息接收函数"""
        self._group_msg_receivers.append(receiver)
        return self

    def on_event(self, receiver: T_EventReceiver):
        """添加事件消息接收函数"""
        self._event_receivers.append(receiver)
        return self

    ########################################################################
    # Add context middlewares
    ########################################################################
    def friend_context_use(self, middleware: T_FriendMsgMiddleware):
        """注册好友消息中间件"""
        self._friend_context_middlewares.append(middleware)
        return self

    def group_context_use(self, middleware: T_GroupMsgMiddleware):
        """注册群消息中间件"""
        self._group_context_middlewares.append(middleware)
        return self

    def event_context_use(self, middleware: T_EventMiddleware):
        """注册事件消息中间件"""
        self._event_context_middlewares.append(middleware)
        return self

    ##########################################################################
    # decorators for registering hook function when connected or disconnected
    ##########################################################################
    def when_connected(self, func: Optional[Callable] = None, *, every_time=False):
        if func is None:
            return functools.partial(self.when_connected, every_time=every_time)
        self._when_connected_do = (func, every_time)
        return None

    def when_disconnected(self, func: Optional[Callable] = None, *, every_time=False):
        if func is None:
            return functools.partial(self.when_disconnected, every_time=every_time)
        self._when_disconnected_do = (func, every_time)
        return None

    ########################################################################
    # about socketio
    ########################################################################
    def _connect(self):
        logger.success("Connected to the server successfully!")

        # 连接成功执行用户定义的函数，如果有
        if self._when_connected_do is not None:
            self._when_connected_do[0]()
            # 如果不需要每次运行，这里运行一次后就废弃设定的函数
            if not self._when_connected_do[1]:
                self._when_connected_do = None

        for func in self.plugMgr.when_connected_funcs:
            self._pool.submit(func, self.qq, self.host, self.port)

    def _disconnect(self):
        logger.warning("Disconnected to the server!")
        # 断开连接后执行用户定义的函数，如果有
        if self._when_disconnected_do is not None:
            self._when_disconnected_do[0]()
            if not self._when_disconnected_do[1]:
                self._when_disconnected_do = None

        for func in self.plugMgr.when_disconnected_funcs:
            self._pool.submit(func, self.qq, self.host, self.port)

    ########################################################################
    # 开放出来的用于多种连接方式的入口函数
    ########################################################################
    def group_msg_handler(self, msg: dict):
        """群消息入口函数
        :param msg: 完整的消息数据
        """
        # 此时plugMgr未初始化，将会出现先打印出消息日志，然后加载插件，打印插件信息
        # 虽然只会在第一条消息时出现这个现象，但这是不符合常理的
        self.plugMgr
        return self._group_msg_handler(msg)

    def friend_msg_handler(self, msg: dict):
        """好友消息入口函数
        :param msg: 完整的消息数据
        """
        self.plugMgr
        return self._friend_msg_handler(msg)

    def event_handler(self, msg: dict):
        """事件入口函数
        :param msg: 完整的消息数据
        """
        self.plugMgr
        return self._event_handler(msg)

    def run(self, wait: bool = True, sio: Optional[socketio.Client] = None):
        """运行
        :param wait: 是否阻塞
        """

        # 调用运行方法了，插件的逻辑是肯定需要的，确保插件逻辑已加载, 这里显式初始化
        self.plugMgr

        sio = sio or socketio.Client()

        sio.event(self._connect)
        sio.event(self._disconnect)
        sio.on("OnGroupMsgs", self._group_msg_handler)
        sio.on("OnFriendMsgs", self._friend_msg_handler)
        sio.on("OnEvents", self._event_handler)

        delay = 1

        try:
            while True:
                try:
                    logger.info(f"Connecting to the server[{self.address}]...")
                    sio.connect(self.address, transports=["websocket"])
                except (SioConnectionError, ValueError):
                    current_delay = delay + (2 * random.random() - 1) / 2
                    logger.error(
                        f"连接失败，请检查ip端口是否配置正确，检查机器人是否启动，确保能够连接上! {current_delay:.1f} 后开始重试连接"
                    )
                    time.sleep(current_delay)
                    delay *= 1.68
                else:
                    break

            self._close_callbacks.append(lambda _: sio.disconnect())

            if wait:
                sio.wait()

        except BaseException as e:
            sio.disconnect()
            self._pool.shutdown(False)
            if isinstance(e, KeyboardInterrupt):
                print("\b\b\b\bbye~")
            else:
                raise

        return sio

    def run_no_wait(self, sio: Optional[socketio.Client] = None):
        """不阻塞运行"""
        return self.run(False, sio)

    def close(self, wait=True):
        for callback in self._close_callbacks:
            callback(wait)
