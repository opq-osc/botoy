import base64
import inspect
import os
import re
import sys
import threading
from functools import wraps
from pathlib import Path
from time import monotonic as clock


def file_to_base64(path):
    """获取文件base64编码"""
    with open(path, "rb") as f:
        content = f.read()
    return base64.b64encode(content).decode()


def check_schema(url: str) -> str:
    url = url.strip("/")
    if not re.findall(r"(http://|https://)", url):
        return "http://" + url
    return url


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

    def permitted(self) -> bool:
        """是否允许调用，即未达到限制次数"""
        with self.lock:
            period_remaining = self.period - (clock() - self.last_reset)

            if period_remaining <= 0:
                self.reset()

            if self.num_calls > self.calls:
                return False

            return True

    def __call__(self, func):
        """装饰该函数，每次调用会自动处理限制
        :param func: 需要装饰的函数
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            self.add(1)
            if self.permitted():
                return func(*args, **kwargs)
            return None

        return wrapper
