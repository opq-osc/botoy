# pylint: disable = too-many-instance-attributes
import copy
import functools
import sys
import traceback
from collections.abc import Sequence
from typing import Any, Callable, List, Optional, Tuple, Union

import socketio

from botoy.config import Config
from botoy.log import enble_log_file, logger
from botoy.model import EventMsg, FriendMsg, GroupMsg
from botoy.plugin import PluginManager
from botoy.pool import WorkerPool

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
    :param friend_whitelist: 好友白名单，只有此名单中的好友消息才会被处理，默认为``空``
    :param blocked_users: 用户黑名单，即包括群消息和好友消息, 该用户的消息都不会处理, 默认为``空``
    :param log: 是否开启日志
    :param log_file: 是否输出日志文件
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
        log_file: bool = True,
    ):
        if qq is not None:
            if isinstance(qq, Sequence):
                self.qq = list(qq)
            else:
                self.qq = [qq]
        else:
            self.qq = None

        self.use_plugins = use_plugins
        self.config = Config(
            host, port, group_blacklist, friend_blacklist, blocked_users
        )

        # 作为程序是否应该退出的标志，以便后续用到
        self._exit = False

        if log:
            if log_file:
                enble_log_file()
        else:
            logger.disable(__name__)

        # 消息接收函数列表
        # 这里只储存主体文件中通过装饰器或函数添加的接收函数
        self._friend_msg_receivers = []
        self._group_msg_receivers = []
        self._event_receivers = []

        # 消息上下文对象中间件列表
        # 中间件以对应消息上下文为唯一参数，返回值与上下文类型一致则向下传递
        # 否则直接丢弃该次消息
        self._friend_context_middlewares = []
        self._group_context_middlewares = []
        self._event_context_middlewares = []

        # 插件管理
        # 管理插件提供的接收函数
        self.plugMgr = PluginManager()
        if use_plugins:
            self.plugMgr.load_plugins()
            print(self.plugin_status)

        # 当连接上或断开连接运行的函数
        # 如果通过装饰器注册了, 这两个字段设置成(func, every_time)
        # func 是需要执行的函数， every_time 表示是否每一次连接或断开都会执行
        self._when_connected_do: Tuple[Callable, bool] = None
        self._when_disconnected_do: Tuple[Callable, bool] = None

        # 线程池 TODO: 开放该参数
        thread_works = 50
        self.pool = WorkerPool(thread_works)

        # 依次各种初始化
        self._initialize_socketio()
        self._initialize_handlers()

    ########################################################################
    # Add context receivers
    ########################################################################
    def on_friend_msg(self, receiver: Callable[[FriendMsg], Any]):
        """添加好友消息接收函数"""
        self._friend_msg_receivers.append(receiver)

    def on_group_msg(self, receiver: Callable[[GroupMsg], Any]):
        """添加群消息接收函数"""
        self._group_msg_receivers.append(receiver)

    def on_event(self, receiver: Callable[[EventMsg], Any]):
        """添加事件消息接收函数"""
        self._event_receivers.append(receiver)

    ########################################################################
    # Add context middlewares
    ########################################################################
    def friend_context_use(
        self, middleware: Callable[[FriendMsg], Optional[FriendMsg]]
    ):
        """注册好友消息中间件"""
        self._friend_context_middlewares.append(middleware)

    def group_context_use(self, middleware: Callable[[GroupMsg], Optional[GroupMsg]]):
        """注册群消息中间件"""
        self._group_context_middlewares.append(middleware)

    def event_context_use(self, middleware: Callable[[EventMsg], Optional[EventMsg]]):
        """注册事件消息中间件"""
        self._event_context_middlewares.append(middleware)

    ########################################################################
    # shortcuts to call plugin manager methods
    ########################################################################
    # 只推荐使用这几个方法，其他的更细致的方法需要通过 plugMgr 对象访问
    # 原始plugMgr提供了自由度更高的方法
    def load_plugins(self):
        '''加载新插件'''
        return self.plugMgr.load_plugins()

    def reload_plugins(self):
        '''重载旧插件，加载新插件'''
        return self.plugMgr.reload_plugins()

    def reload_plugin(self, plugin_name: str):
        '''重载指定插件'''
        return self.plugMgr.reload_plugin(plugin_name)

    def remove_plugin(self, plugin_name: str):
        '''停用指定插件'''
        return self.plugMgr.remove_plugin(plugin_name)

    def recover_plugin(self, plugin_name: str):
        '''启用指定插件'''
        return self.plugMgr.recover_plugin(plugin_name)

    @property
    def plugin_status(self):
        '''插件启用状态'''
        return self.plugMgr.info_table

    @property
    def plugins(self):
        '''插件名列表'''
        return self.plugMgr.plugins

    @property
    def removed_plugins(self):
        '''已停用的插件名列表'''
        return self.plugMgr.removed_plugins

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
        logger.success('Connected to the server successfully!')

        # 连接成功执行用户定义的函数，如果有
        if self._when_connected_do is not None:
            self._when_connected_do[0]()
            # 如果不需要每次运行，这里运行一次后就废弃设定的函数
            if not self._when_connected_do[1]:
                self._when_connected_do = None

    def disconnect(self):
        logger.warning('Disconnected to the server!')
        # 断开连接后执行用户定义的函数，如果有
        if self._when_disconnected_do is not None:
            self._when_disconnected_do[0]()
            if not self._when_disconnected_do[1]:
                self._when_disconnected_do = None

    def close(self, status=0):
        self.socketio.disconnect()
        self.pool.shutdown(wait=False)
        self._exit = True
        sys.exit(status)

    def run(self):
        logger.info('Connecting to the server...')
        try:
            self.socketio.connect(self.config.address, transports=['websocket'])
        except Exception:
            logger.error(traceback.format_exc())
            self.close(1)
        else:
            try:
                self.socketio.wait()
            except KeyboardInterrupt:
                pass
            finally:
                print('bye~')
                self.close(0)

    ########################################################################
    # context distributor
    ########################################################################
    def _friend_context_distributor(self, context: FriendMsg):
        for f_receiver in [
            *self._friend_msg_receivers,
            *self.plugMgr.friend_msg_receivers,
        ]:
            self.pool.submit(f_receiver, copy.deepcopy(context))

    def _group_context_distributor(self, context: GroupMsg):
        for g_receiver in [
            *self._group_msg_receivers,
            *self.plugMgr.group_msg_receivers,
        ]:
            self.pool.submit(g_receiver, copy.deepcopy(context))

    def _event_context_distributor(self, context: EventMsg):
        for e_receiver in [
            *self._event_receivers,
            *self.plugMgr.event_receivers,
        ]:
            self.pool.submit(e_receiver, copy.deepcopy(context))

    ########################################################################
    # message handler
    ########################################################################
    def _friend_msg_handler(self, msg):
        context = FriendMsg(msg)
        if self.qq and context.CurrentQQ not in self.qq:
            return
        logger.info(f'{context.__class__.__name__} ->  {context.data}')
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
        self.pool.submit(self._friend_context_distributor, context)

    def _group_msg_handler(self, msg):
        context = GroupMsg(msg)
        if self.qq and context.CurrentQQ not in self.qq:
            return
        logger.info(f'{context.__class__.__name__} ->  {context.data}')
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
        self.pool.submit(self._group_context_distributor, context)

    def _event_handler(self, msg):
        context = EventMsg(msg)
        if self.qq and context.CurrentQQ not in self.qq:
            return
        logger.info(f'{context.__class__.__name__} ->  {context.data}')
        # 中间件
        if self._event_context_middlewares:
            for middleware in self._event_context_middlewares:
                new_context = middleware(context)
                if isinstance(new_context, type(context)):
                    context = new_context
                else:
                    return
        self.pool.submit(self._event_context_distributor, context)

    ########################################################################
    # initialize
    ########################################################################
    def _initialize_socketio(self):
        self.socketio = socketio.Client()
        self.socketio.event()(self.connect)
        self.socketio.event()(self.disconnect)

    def _initialize_handlers(self):
        self.socketio.on('OnGroupMsgs')(self._group_msg_handler)
        self.socketio.on('OnFriendMsgs')(self._friend_msg_handler)
        self.socketio.on('OnEvents')(self._event_handler)

    ########################################################################
    def __repr__(self):
        return 'Botoy <{}> <host-{}> <port-{}> <address-{}>'.format(
            " ".join([str(i) for i in self.qq]),
            self.config.host,
            self.config.port,
            self.config.address,
        )
