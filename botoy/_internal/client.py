import asyncio
import importlib
import inspect
import os
import re
import signal
import threading
import traceback
from contextvars import copy_context
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union
from urllib.parse import urlparse
from uuid import uuid4

import prettytable
from websockets.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed, InvalidURI

from . import runner
from .config import jconfig
from .context import Context, ctx_var
from .log import logger
from .pool import WorkerPool


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
        该信息仅用于开发者调试
        :param receiver: 接收函数
        :param name: 插件名称，默认为__name__
        :param author: 插件作者，默认为空
        :param usage: 插件用法，默认为__doc__
        """
        receiver.__dict__["is_receiver"] = True
        meta = ""
        if file := inspect.getsourcefile(receiver):
            meta += str(Path(file).relative_to(os.getcwd()))
        try:
            lines = inspect.getsourcelines(receiver)
            if meta:
                meta += " line {}".format(lines[1])
        except:
            pass

        receiver.__dict__["receiver_info"] = {
            "author": author or "",
            "usage": usage or receiver.__doc__ or "",
            "name": name or receiver.__name__ or "",
            "meta": meta or "",
        }

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
        return receiver.__dict__.get("is_receiver", False)
    except Exception:
        return False


#####################


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
        self.handlers = []
        self.state = "disconnected"
        self.loaded_plugins = False
        self.pool = WorkerPool(50)
        self._url = self._get_ws_url(jconfig.url)

    @property
    def connection_url(self):
        return self._url

    def set_url(self, url: str):
        self._url = self._get_ws_url(url)

    def load_plugins(self):
        """加载插件"""
        if self.loaded_plugins:
            raise RuntimeError("插件只能加载一次")
        self.loaded_plugins = True

        # 哪些可能是插件
        # 1. 所有.py文件
        # 2. 所有包目录
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
                if is_recv(v):
                    self.attach(v)

    def print_receivers(self):
        """在控制台打印接收函数信息"""
        table = prettytable.PrettyTable(["Name", "Author", "Usage", "Meta"])
        for _, receiver_info in self.handlers:
            table.add_row(
                [
                    receiver_info.get("name", ""),
                    receiver_info.get("author", ""),
                    receiver_info.get("usage", ""),
                    receiver_info.get("meta", ""),
                ]
            )
        print(table)

    def attach(self, receiver):
        """绑定接收函数
        :param receiver: 消息接收函数
        """
        if receiver in (i[0] for i in self.handlers):
            return
        #  不使用插件，基本不会调用mark_recv，这里自动调用补充默认信息
        if not hasattr(receiver, "receiver_info"):
            mark_recv(receiver, _directly_attached=True)
        info = getattr(receiver, "receiver_info", {})

        async def handler():
            try:
                ctx = copy_context()
                if asyncio.iscoroutinefunction(receiver):
                    return await receiver()
                else:
                    return await asyncio.get_running_loop().run_in_executor(
                        self.pool, lambda: ctx.run(receiver)
                    )
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.error("接收函数中出现错误：\n" + traceback.format_exc())

        self.handlers.append((handler, info))

    __call__ = attach

    async def _packet_handler(self, pkt, __available_names: Optional[List[str]] = None):
        # __available_names 用于mahiro管理
        # 当前的实现，副作用：增加一项要求: 接收函数有 name 并且 name 唯一
        # TODO: 在mark_recv中处理好name
        # 由botoy注册的框架名自动添加 BOTOY前缀如："name" => "BOTOY name"
        if __available_names is not None:
            __available_names = [i[6:] for i in __available_names]
            token = ctx_var.set(Context(pkt))
            await asyncio.gather(
                *(
                    self._start_task(receiver)
                    for (receiver, info) in self.handlers
                    if info.get("name", "") in __available_names
                ),
            )
            ctx_var.reset(token)

    def _start_task(self, target, *args, **kwargs):
        return asyncio.ensure_future(target(*args, **kwargs))

    async def _read_loop(self):
        while self.state == "connected":
            try:
                if self.ws is not None:
                    async for pkt in self.ws:
                        if self.handlers:
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
            try:
                logger.info(f"连接中[{self.connection_url}]...")
                self.state = "connecting"
                ws = await ws_connect(self.connection_url, open_timeout=5)
            except InvalidURI as e:
                logger.error(f"连接地址有误: {e}")
                await asyncio.sleep(2)
            except asyncio.TimeoutError as e:
                logger.error(f"连接超时: {e}")
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"连接失败: {e}")
                await asyncio.sleep(2)
            else:
                logger.success("连接成功!")
                break

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

    def _get_ws_url(self, url: str) -> str:
        if not re.match(r"$(http|https|ws)://", url):
            url = "ws://" + url
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        # print(parsed_url)
        assert hostname, f"{url} 有误，请检查!"
        port = parsed_url.port
        return f"ws://{hostname}{ ':'+ str(port) if port is not None else ''}/ws"
