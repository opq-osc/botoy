"""
该模块提供一系列内置辅助功能
"""

# NOTE: 这是独立的模块，不应该在框架其他位置被导入，以免循环依赖
import asyncio
import base64
import contextvars
import inspect
import os
import sys
import threading
from asyncio import events
from functools import partial, wraps
from pathlib import Path
from time import monotonic as clock
from typing import Any, Awaitable, Callable, Dict, Optional, Union

import httpx

from .typing import T_GeneralReceiver

__all__ = [
    "file_to_base64",
    "get_cache_dir",
    "RateLimit",
    "Switcher",
    "SwitcherManager",
    "async_run",
    "download",
    "to_async",
]


def file_to_base64(path):
    """获取文件base64编码"""
    with open(path, "rb") as f:
        content = f.read()
    return base64.b64encode(content).decode()


def get_cache_dir(dir_name: str) -> Path:
    """获取缓存目录
    :param dir_name: 目录(文件夹)名
    :return: 返回对应目录的Path对象
    """
    # 确定主缓存目录
    for i in os.listdir(Path(".")):
        if i in ["botoy.json", "REMOVED_PLUGINS", "bot.py", "plugins"]:
            main_dir = Path(".")
            break
    else:
        cf = inspect.currentframe()
        bf = cf.f_back  # type:ignore
        file = bf.f_globals["__file__"]  # type:ignore
        dir_ = Path(file).absolute()
        while "plugins" in str(dir_):
            dir_ = dir_.parent
            if dir_.name == "plugins":
                main_dir = dir_.parent
                break
        else:
            main_dir = Path(".")

    cache_dir = main_dir / "botoy-cache"
    if not cache_dir.exists():
        cache_dir.mkdir()

    this_cache_dir = cache_dir / dir_name
    if not this_cache_dir.exists():
        os.makedirs(this_cache_dir)
    return this_cache_dir.absolute()


class RateLimit:
    """速率控制"""

    def __init__(self, calls: int, period: int):
        """
        :param int calls: 时间段内运行调用的最大次数
        :param int period: 时间间隔，单位为秒
        """
        self.calls = max(1, min(sys.maxsize, int(calls)))
        self.period = period

        # states
        self.last_reset = clock()
        self.num_calls = 0

        self.lock = threading.RLock()

    def add(self, num_calls: int = 1):
        """增加当前已调用次数
        :param int num_calls: 需要增加的调用次数
        """
        with self.lock:
            self.num_calls += num_calls

    def reset(self):
        """重置当前状态, 将重新统计调用次数"""
        with self.lock:
            self.num_calls = 0
            self.last_reset = clock()

    @property
    def left_calls(self) -> int:
        """剩余可调用次数"""
        if self.num_calls >= self.calls:
            return 0
        return self.calls - self.num_calls

    def permitted(self) -> bool:
        """是否允许调用，即未达到限制次数"""
        with self.lock:
            period_remaining = self.period - (clock() - self.last_reset)

            if period_remaining <= 0:
                self.reset()

            if self.num_calls >= self.calls:
                return False

            return True

    def __call__(self, func):
        """装饰该函数，每次调用会自动处理限制
        :param func: 需要装饰的函数
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.permitted():
                self.add(1)
                return func(*args, **kwargs)
            return None

        return wrapper


class Switcher:
    """一个简单的开关"""

    __slots__ = ("_enabled",)

    def __init__(self, init_enabled: bool = False):
        """
        :param init_enabled: 初始的开关状态
        """
        self._enabled = init_enabled

    def enable(self):
        """开启"""
        self._enabled = True

    def disable(self):
        """关闭"""
        self._enabled = False

    def toggle(self):
        """切换开关"""
        self._enabled = not self._enabled

    @property
    def enabled(self) -> bool:
        """是否开启"""
        return self._enabled

    def __bool__(self) -> bool:
        """是否开启"""
        return self._enabled


# TODO: 缓存至文件，否则每次启动都是重置状态，没有实用性
class SwitcherManager:
    """开关管理器"""

    __slots__ = ("name", "init_enabled")
    storage: Dict[str, Switcher] = {}

    def __init__(self, name: str, init_enabled: bool = True):
        """
        :param name: 开关管理器的唯一标识符, 这往往对应一个单独的功能或插件
        :param init_enabled: 默认是开或关
        """
        self.name = name
        self.init_enabled = init_enabled

    def of(self, id: Optional[Union[int, str]] = None) -> Switcher:
        """获取开关
        :param id: 开关的标识符, 未指定则返回默认的开关
        """
        if id is None:
            key = self.name
        else:
            key = f"{self.name}-{id}"
        if key not in self.storage:
            self.storage[key] = Switcher(self.init_enabled)
        return self.storage[key]


def download(
    url: str, dist: Union[str, Path], timeout: int = 20, status: bool = True, **kwargs
):
    """下载文件
    :param url: 文件URL
    :param dist: 下载保存路径
    :param timeout: 请求连接超时时间
    :param status: 是否显示当前进度
    :param kwargs: 额外传入httpx.stream中的参数，如headers
    :return: 无返回，下载失败则报相关错误
    """
    if isinstance(dist, str):
        dist = Path(dist)
    try:
        with httpx.stream("GET", url, timeout=timeout, **kwargs) as resp:
            try:
                total = int(resp.headers["content-length"])
            except:
                total = None

            print(f"正在下载: {dist}")

            downloaded = -512
            with open(dist, "wb") as f:
                for chunk in resp.iter_bytes(512):
                    f.write(chunk)
                    downloaded += 512

                    if status and total:
                        percent = int(100 * downloaded / total)
                        print("\r|{:100}|{}%".format("#" * percent, percent), end="")
                if status and total:
                    print("\r|{:100}|{}%".format("#" * 100, 100))
    except Exception as e:
        if dist.exists():
            os.remove(dist)
        raise e


def to_async(func: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
    """将函数包装为异步函数
    :param func: 被装饰的同步函数
    """

    @wraps(func)
    async def _wrapper(*args: Any, **kwargs: Any) -> Any:
        loop = events.get_running_loop()
        ctx = contextvars.copy_context()
        func_call = partial(ctx.run, func, *args, **kwargs)
        return await loop.run_in_executor(None, func_call)

    return _wrapper


async def async_run(func, *args, **kwargs):
    """异步执行函数
    提供的任何 *args 和 **kwargs 会被直接传给 func

    :param func: 目标函数
    """
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    loop = events.get_running_loop()
    ctx = contextvars.copy_context()
    func_call = partial(ctx.run, func, *args, **kwargs)
    return await loop.run_in_executor(None, func_call)


def sync_run(func):
    """同步执行异步函数，获取结果(该函数始终新建一个事件循环)
    例如::

        async def hello(name=None):
            if name:
                return f'Hello {name}'
            return 'Hello'


        print(sync_run(hello()))  # Hello
        print(sync_run(hello('World')))  # Hello World
    """
    loop = asyncio.new_event_loop()
    coro = asyncio.iscoroutine(func) and func or func()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class _PluginReceiver:
    """插件接收器助手"""

    def __init__(self, stack=2):
        self.__group = []
        self.__friend = []
        self.__event = []

        self.__stack = stack

    def __set_globals(self, name, value):
        f = inspect.currentframe()
        for _ in range(self.__stack):
            f = f.f_back  # type: ignore
        f.f_globals[name] = value  # type: ignore

    def __sync_group(self, ctx):
        for func in self.__group:
            func(ctx)

    async def __async_group(self, ctx):
        for func in self.__group:
            if asyncio.iscoroutinefunction(func):
                await func(ctx)
            else:
                func(ctx)

    def __sync_friend(self, ctx):
        for func in self.__friend:
            func(ctx)

    async def __async_friend(self, ctx):
        for func in self.__friend:
            if asyncio.iscoroutinefunction(func):
                await func(ctx)
            else:
                func(ctx)

    def __sync_event(self, ctx):
        for func in self.__event:
            func(ctx)

    async def __async_event(self, ctx):
        for func in self.__event:
            if asyncio.iscoroutinefunction(func):
                await func(ctx)
            else:
                func(ctx)

    def group(self, func):
        # 因为异步接收器可能不是第一个添加，所以每次添加异步接收器时
        # 都设置插件的接收函数为异步
        # 默认是同步, 当第一次添加时设置一次足够了
        if asyncio.iscoroutinefunction(func):
            self.__set_globals("receive_group_msg", self.__async_group)
        elif len(self.__group) == 0:
            self.__set_globals("receive_group_msg", self.__sync_group)
        assert func not in self.__group, "重复添加不合常理, 直接报错"
        self.__group.append(func)
        return func

    def friend(self, func):
        if asyncio.iscoroutinefunction(func):
            self.__set_globals("receive_friend_msg", self.__async_friend)
        elif len(self.__friend) == 0:
            self.__set_globals("receive_friend_msg", self.__sync_friend)
        assert func not in self.__friend, "重复添加不合常理, 直接报错"
        self.__friend.append(func)
        return func

    def event(self, func):
        if asyncio.iscoroutinefunction(func):
            self.__set_globals("receive_events", self.__async_event)
        elif len(self.__event) == 0:
            self.__set_globals("receive_events", self.__sync_event)
        assert func not in self.__event, "重复添加不合常理, 直接报错"
        self.__event.append(func)
        return func


# 进一步封装PluginReceiver, 省去单独定义对象的步骤
class plugin_receiver:
    @classmethod
    def __get_instance(cls):
        f_globals = inspect.currentframe().f_back.f_back.f_globals  # type: ignore
        instance = f_globals.get("__plugin_receiver__")
        if instance is None:
            instance = _PluginReceiver(3)
            f_globals["__plugin_receiver__"] = instance
        return instance

    @classmethod
    def group(cls, func: T_GeneralReceiver) -> T_GeneralReceiver:
        """添加群消息接收器到该插件的运行队列里"""
        return cls.__get_instance().group(func)

    @classmethod
    def friend(cls, func: T_GeneralReceiver) -> T_GeneralReceiver:
        """添加好友消息接收器到该插件的运行队列里"""
        return cls.__get_instance().friend(func)

    @classmethod
    def event(cls, func: T_GeneralReceiver) -> T_GeneralReceiver:
        """添加事件消息接收器到该插件的运行队列里"""
        return cls.__get_instance().event(func)
