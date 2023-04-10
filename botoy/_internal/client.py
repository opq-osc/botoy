import asyncio
import importlib
import inspect
import os
import re
import signal
import sys
import threading
import traceback
from contextvars import copy_context
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from uuid import uuid4

import prettytable
from websockets.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed, InvalidURI

from .config import jconfig
from .context import Context, ctx_var
from .log import logger
from .pool import WorkerPool

connected_clients = []

is_signal_hander_set = False


def async_signal_handler():
    async def _handler():
        for c in connected_clients[:]:
            await c.disconnect()

    asyncio.ensure_future(_handler())


def mark_recv(receiver, name="", author="", usage="", *, __directly_attached=False):
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

    # 插件通过加入额外信息标记接收函数, 其前提该函数能在import后的module中**被检索**到
    # 被attach调用时，函数会被直接添加，所以无需进行该操作
    if not __directly_attached:
        back_globals = inspect.currentframe().f_back.f_globals  # type: ignore
        if receiver not in back_globals.values():
            u = "receiver" + str(uuid4())
            back_globals[u] = receiver


def is_recv(receiver):
    try:
        return receiver.__dict__.get("is_receiver", False)
    except Exception:
        return False


class Botoy:
    def __init__(self):
        self.ws = None
        self.handlers = []
        self.state = "disconnected"
        self.loaded_plugins = False
        self.pool = WorkerPool(50)

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
            mark_recv(receiver, __directly_attached=True)
        info = getattr(receiver, "receiver_info", {})

        async def handler():
            try:
                ctx = copy_context()
                if asyncio.iscoroutinefunction(receiver):
                    await receiver()
                else:
                    await asyncio.get_running_loop().run_in_executor(
                        self.pool, lambda: ctx.run(receiver)
                    )
            except Exception:
                logger.error("接收函数中出现错误：\n" + traceback.format_exc())

        self.handlers.append((handler, info))

    __call__ = attach

    def _start_task(self, target, *args, **kwargs):
        return asyncio.ensure_future(target(*args, **kwargs))

    async def _read_loop(self):
        while self.state == "connected":
            try:
                if self.ws is not None:
                    async for pkt in self.ws:
                        token = ctx_var.set(Context(pkt))  # type: ignore
                        await asyncio.gather(
                            *[
                                self._start_task(receiver)
                                for (receiver, *_) in self.handlers
                            ]
                        )
                        ctx_var.reset(token)
            except ConnectionClosed:
                connected_clients.remove(self)
                if self.state == "connected":
                    self.reconnect_task = self._start_task(self._handle_reconnect)
                break

    async def connect(self, url=None, hot_reload=False):
        self.connection_url = self._get_ws_url(url or jconfig.url)
        self.hot_reload = hot_reload

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
            await self.connect(self.connection_url, self.hot_reload)
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

    def _get_ws_url(self, url: str) -> str:
        if not re.match(r"$(http|https|ws)://", url):
            url = "ws://" + url
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        # print(parsed_url)
        assert hostname, f"{url} 有误，请检查!"
        port = parsed_url.port
        return f"ws://{hostname}{ ':'+ str(port) if port is not None else ''}/ws"
