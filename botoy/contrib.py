"""
该模块提供一系列内置辅助功能
"""

# NOTE: 这是独立的模块，不应该在框架其他位置被导入，以免循环依赖
import base64
import inspect
import os
import re
import sys
import threading
from functools import wraps
from pathlib import Path
from time import monotonic as clock
from typing import Dict, Union

__all__ = [
    "file_to_base64",
    "get_cache_dir",
    "RateLimit",
    "Switcher",
    "SwitcherManager",
]


def file_to_base64(path):
    """获取文件base64编码"""
    with open(path, "rb") as f:
        content = f.read()
    return base64.b64encode(content).decode()


def get_cache_dir(dir_name: str) -> Path:
    """获取缓存目录
    :param dir_name: the cache directory's name.
    :return: A Path object of the cache directory
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
    return this_cache_dir


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

    def of(self, id: Union[int, str] = None) -> Switcher:
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
