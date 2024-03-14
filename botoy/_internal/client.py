import asyncio
import importlib
import inspect
import re
import signal
import threading
from pathlib import Path
from typing import Callable, List, Optional
from urllib.parse import urlparse

import prettytable
from websockets.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed, InvalidURI

from . import runner
from .config import jconfig
from .context import Context, current_ctx
from .keys import *
from .log import logger
from .pool import WorkerPool
from .receiver import Receiver, ReceiverInfo, is_recv, mark_recv

connected_clients = []
is_signal_hander_set = False


def async_signal_handler():
    async def _handler():
        for c in connected_clients[:]:
            await c.disconnect()

        tasks = [
            task for task in asyncio.all_tasks() if task is not asyncio.current_task()
        ]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        asyncio.get_event_loop().stop()

    asyncio.ensure_future(_handler())


class Botoy:
    def __init__(self):
        self.ws = None
        self.receivers: List[Receiver] = []
        self.state = "disconnected"
        self.loaded_plugins = False
        self.pool = WorkerPool()
        self.connection_urls = self._get_ws_urls(jconfig.url)

    def set_url(self, url: str):
        self.connection_urls = self._get_ws_urls(url)

    def load_plugins(self):
        """加载插件"""
        if self.loaded_plugins:
            raise RuntimeError("插件只能加载一次")
        self.loaded_plugins = True

        # 哪些可能是插件
        # 1. 所有.py文件
        # 2. 所有包目录
        # 插件提供接收函数，扫描所有接收函数
        # 哪些是接收函数
        # 1. 被mark_recv包装过的所有可调用对象
        # 2. 命名以r_开头的所有函数
        mods = []
        plugins_dir = Path("plugins")
        for path in plugins_dir.iterdir():
            if (path.is_file() and path.suffix.lower() == ".py") or (
                path.is_dir()
                and ((path / "__init__.py").exists() or (path / "__init__.PY").exists())
            ):
                mods.append(f"plugins.{path.stem}")

        # 检索receiver
        for mod in mods:
            module = importlib.import_module(mod)
            # print(module.__dict__.keys())
            for v in module.__dict__.values():
                if isinstance(v, Callable):
                    if is_recv(v) or (
                        inspect.isfunction(v) and v.__name__.startswith("r_")
                    ):
                        self.attach(v)

    def print_receivers(self):
        """在控制台打印接收函数信息"""
        table = prettytable.PrettyTable(["Name", "Author", "Usage", "Meta"])
        for receiver in self.receivers:
            info = receiver.info
            table.add_row([info.name, info.author, info.usage, info.meta])
        print(table)

    def attach(self, callback):
        """绑定接收函数
        :param callback: 消息接收函数
        """
        if callback in (i.callback for i in self.receivers):
            return
        #  不使用插件，基本不会调用mark_recv，这里自动调用补充默认信息
        if not hasattr(callback, RECEIVER_INFO):
            mark_recv(callback, _directly_attached=True)
        info = getattr(callback, RECEIVER_INFO, ReceiverInfo())

        receiver = Receiver(callback, info, pool=self.pool)
        self.receivers.append(receiver)

    __call__ = attach

    async def _packet_handler(self, pkt, _available_names: Optional[List[str]] = None):
        # __available_names 用于mahiro管理
        # 当前的实现，副作用：增加一项要求: 接收函数有 name 并且 name 唯一
        # TODO: 在mark_recv中处理好name
        # 由botoy注册的框架名自动添加 BOTOY前缀如："name" => "BOTOY name"
        token = current_ctx.set(Context(pkt))
        if _available_names is not None:
            _available_names = [i[6:] for i in _available_names]
            await asyncio.gather(
                *(
                    self._start_task(receiver)
                    for receiver in self.receivers
                    if receiver.info.name in _available_names
                ),
                return_exceptions=True,
            )
        else:
            await asyncio.gather(
                *(self._start_task(receiver) for receiver in self.receivers),
                return_exceptions=True,
            )
        current_ctx.reset(token)

    def _start_task(self, target, *args, **kwargs):
        return asyncio.ensure_future(target(*args, **kwargs))

    async def _read_loop(self):
        while self.state == "connected":
            try:
                if self.ws is not None:
                    async for pkt in self.ws:
                        if self.receivers:
                            self._start_task(self._packet_handler, pkt)
            except ConnectionClosed:
                connected_clients.remove(self)
                if self.state == "connected":
                    self.reconnect_task = self._start_task(self._handle_reconnect)
                break

    async def connect(self):
        global is_signal_hander_set
        if (
            not is_signal_hander_set
            and threading.current_thread() == threading.main_thread()
        ):
            try:
                asyncio.get_event_loop().add_signal_handler(
                    signal.SIGINT, async_signal_handler
                )
            except NotImplementedError:
                pass
            is_signal_hander_set = True

        ws = None
        while True:
            for idx, connection_url in enumerate(self.connection_urls):
                try:
                    if idx == 0:
                        logger.info(f"正在连接[{connection_url}]...")
                    else:
                        logger.info(f"尝试连接[{connection_url}]...")
                    self.state = "connecting"
                    ws = await ws_connect(connection_url, open_timeout=3)
                except InvalidURI as e:
                    logger.error(f"连接地址有误[{connection_url}]: {e}")
                except asyncio.TimeoutError as e:
                    logger.error(f"连接超时[{connection_url}]: {e}")
                except Exception as e:
                    logger.error(f"连接失败[{connection_url}]: {e}")
                else:
                    self.connection_urls.remove(connection_url)
                    self.connection_urls.insert(0, connection_url)
                    logger.success(f"连接成功[{connection_url}]!")
                    break
                await asyncio.sleep(1)
            if ws:
                break
            await asyncio.sleep(1)

        if ws:
            self.state = "connected"
            connected_clients.append(self)
            self.ws = ws
            self._start_task(self._read_loop)

    async def disconnect(self):
        if self.ws and not self.ws.closed:
            self.state = "disconnecting"
            await self.ws.close()
            self.state = "disconnected"
            connected_clients.remove(self)

    async def _handle_reconnect(self):
        logger.info("准备重连中...")
        try:
            await self.connect()
        except:
            pass
        else:
            self.reconnect_task = None

    async def wait(self):
        while True:
            if not self.ws:
                break
            await self.ws.wait_closed()
            await asyncio.sleep(1)
            if not self.reconnect_task:
                break
            await self.reconnect_task
            if self.state != "connected":
                break

    def run(self, reload=False):
        """一键启动
        :param reload: 开启热重载
        """
        runner.run(self, reload)

    def _get_ws_urls(self, url: str) -> List[str]:
        if not re.match(r"^(http|https|ws|wss)://", url):
            url = "ws://" + url
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme
        hostname = parsed_url.hostname
        port = parsed_url.port
        assert hostname, f"{url} 有误，请检查!"
        schemes = ["ws", "wss"] if scheme in ["http", "ws"] else ["wss", "ws"]
        return [
            f"{s}://{hostname}{ ':'+  str(port) if port  else ''}/ws" for s in schemes
        ]
