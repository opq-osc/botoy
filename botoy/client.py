# pylint: disable = too-many-instance-attributes, W0212
import copy
import functools
import traceback
from collections.abc import Sequence
from typing import Callable, List, Optional, Tuple, Union

import socketio

from .config import Config
from .log import logger, logger_init
from .model import EventMsg, FriendMsg, GroupMsg
from .plugin import PluginManager
from .pool import WorkerPool
from .typing import (
    T_EventMiddleware,
    T_EventReceiver,
    T_FriendMsgMiddleware,
    T_FriendMsgReceiver,
    T_GroupMsgMiddleware,
    T_GroupMsgReceiver,
)

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
                所有信息，如果传了，则只会接收对应机器人的信息
    :param use_plugins: 是否开启插件功能, 默认``False``
    :param port: 运行端口, 默认为``8888``
    :param host: ip，默认为``http://127.0.0.1``
    :param group_blacklist: 群黑名单, 此名单中的群聊消息不会被处理,默认为``空``
    :param friend_blacklist: 好友黑名单，此名单中的好友消息不会被处理，默认为``空``
    :param blocked_users: 用户黑名单，即包括群消息和好友消息, 该用户的消息都不会处理, 默认为``空``
    :param log: 该参数控制控制台日志等级,为True输出INFO等级日志,为False输出EROOR等级的日志
    :param log_file: 该参数控制日志文件开与关,为True输出INFO等级日志的文件,为False关闭输出日志文件
    """

    def __init__(
        self,
        *,
        qq: Union[int, List[int]] = None,
        use_plugins: bool = False,
        port: int = None,
        host: str = None,
        group_blacklist: List[int] = None,
        friend_blacklist: List[int] = None,
        blocked_users: List[int] = None,
        log: bool = True,
        log_file: bool = False,
    ):
        if qq is not None:
            if isinstance(qq, Sequence):
                self.qq = list(qq)
            else:
                self.qq = [qq]
        else:
            self.qq = []

        self.config = Config(
            host, port, group_blacklist, friend_blacklist, blocked_users
        )

        # 日志
        logger_init(log, log_file)

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
        if self.config.webhook:
            from . import webhook  # pylint: disable=C0415

            self._friend_msg_receivers.append(webhook.receive_friend_msg)
            self._group_msg_receivers.append(webhook.receive_group_msg)
            self._event_receivers.append(webhook.receive_events)

        # 插件管理
        # 管理插件提供的接收函数
        self.plugMgr = PluginManager()
        if use_plugins:
            self.plugMgr.load_plugins()
            print(self.plugMgr.info)

        # 当连接上或断开连接运行的函数
        # 如果通过装饰器注册了, 这两个字段设置成(func, every_time)
        # func 是需要执行的函数， every_time 表示是否每一次连接或断开都会执行
        self._when_connected_do: Optional[Tuple[Callable, bool]] = None
        self._when_disconnected_do: Optional[Tuple[Callable, bool]] = None

        # 线程池 TODO: 开放该参数
        thread_works = 50
        self.pool = WorkerPool(thread_works)

    ########################################################################
    # Add context receivers
    ########################################################################
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
    def when_connected(self, func: Callable = None, *, every_time=False):
        if func is None:
            return functools.partial(self.when_connected, every_time=every_time)
        self._when_connected_do = (func, every_time)
        return None

    def when_disconnected(self, func: Callable = None, *, every_time=False):
        if func is None:
            return functools.partial(self.when_disconnected, every_time=every_time)
        self._when_disconnected_do = (func, every_time)
        return None

    ########################################################################
    # about socketio
    ########################################################################
    def connect(self):
        logger.success("Connected to the server successfully!")

        # 连接成功执行用户定义的函数，如果有
        if self._when_connected_do is not None:
            self._when_connected_do[0]()
            # 如果不需要每次运行，这里运行一次后就废弃设定的函数
            if not self._when_connected_do[1]:
                self._when_connected_do = None

    def disconnect(self):
        logger.warning("Disconnected to the server!")
        # 断开连接后执行用户定义的函数，如果有
        if self._when_disconnected_do is not None:
            self._when_disconnected_do[0]()
            if not self._when_disconnected_do[1]:
                self._when_disconnected_do = None

    ########################################################################
    # context distributor
    ########################################################################
    def _friend_context_distributor(self, context: FriendMsg):
        for f_receiver in [
            *self._friend_msg_receivers,
            *self.plugMgr.friend_msg_receivers,
        ]:
            distributive_context = copy.deepcopy(context)
            self.pool.submit(f_receiver, distributive_context)

    def _group_context_distributor(self, context: GroupMsg):
        for g_receiver in [
            *self._group_msg_receivers,
            *self.plugMgr.group_msg_receivers,
        ]:
            distributive_context = copy.deepcopy(context)
            self.pool.submit(g_receiver, distributive_context)

    def _event_context_distributor(self, context: EventMsg):
        for e_receiver in [
            *self._event_receivers,
            *self.plugMgr.event_receivers,
        ]:
            distributive_context = copy.deepcopy(context)
            self.pool.submit(e_receiver, distributive_context)

    ########################################################################
    # message handler
    ########################################################################
    def _friend_msg_handler(self, msg):
        context = FriendMsg(msg)
        if self.qq and context.CurrentQQ not in self.qq:
            return
        logger.info(f"{context.__class__.__name__} ->  {context.data}")
        # 黑名单
        if context.FromUin in self.config.friend_blacklist:
            return
        # 屏蔽用户
        if context.FromUin in self.config.blocked_users:
            return
        # 中间件
        if self._friend_context_middlewares:
            for middleware in self._friend_context_middlewares:
                new_context = middleware(context)
                if isinstance(new_context, type(context)):
                    context = new_context
                else:
                    return
        # 传递几个数据供(插件中的)接收函数调用, 其他不再注释
        setattr(context, "_host", self.config.host)
        setattr(context, "_port", self.config.port)
        self.pool.submit(self._friend_context_distributor, context)

    def _group_msg_handler(self, msg):
        context = GroupMsg(msg)
        if self.qq and context.CurrentQQ not in self.qq:
            return
        logger.info(f"{context.__class__.__name__} ->  {context.data}")
        # 黑名单
        if context.FromGroupId in self.config.group_blacklist:
            return
        # 屏蔽用户
        if context.FromUserId in self.config.blocked_users:
            return
        # 中间件
        if self._group_context_middlewares:
            for middleware in self._group_context_middlewares:
                new_context = middleware(context)
                if isinstance(new_context, type(context)):
                    context = new_context
                else:
                    return
        setattr(context, "_host", self.config.host)
        setattr(context, "_port", self.config.port)
        self.pool.submit(self._group_context_distributor, context)

    def _event_handler(self, msg):
        context = EventMsg(msg)
        if self.qq and context.CurrentQQ not in self.qq:
            return
        logger.info(f"{context.__class__.__name__} ->  {context.data}")
        # 中间件
        if self._event_context_middlewares:
            for middleware in self._event_context_middlewares:
                new_context = middleware(context)
                if isinstance(new_context, type(context)):
                    context = new_context
                else:
                    return
        setattr(context, "_host", self.config.host)
        setattr(context, "_port", self.config.port)
        self.pool.submit(self._event_context_distributor, context)

    def run(self):
        sio = socketio.Client()

        sio.event(self.connect)
        sio.event(self.disconnect)
        sio.on("OnGroupMsgs")(self._group_msg_handler)
        sio.on("OnFriendMsgs")(self._friend_msg_handler)
        sio.on("OnEvents")(self._event_handler)

        logger.info("Connecting to the server...")
        try:
            sio.connect(self.config.address, transports=["websocket"])
        except Exception:
            logger.error(traceback.format_exc())
            sio.disconnect()
            self.pool.shutdown(wait=False)
        else:
            try:
                sio.wait()
            except KeyboardInterrupt:
                pass
            finally:
                print("bye~")
                sio.disconnect()
                self.pool.shutdown(wait=False)
