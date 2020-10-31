import functools
import time
from collections import defaultdict
from threading import Lock

_lock_dict = defaultdict(Lock)


def queued_up(func=None, *, name='default'):
    """队列执行函数
    :param name: 指定队列分组, 不同的名称用不同的队列
    """
    if func is None:
        return functools.partial(queued_up, name=name)

    def inner(ctx):
        lock = _lock_dict[repr(name)]
        try:
            lock.acquire()
            ret = func(ctx)
            # 为了易用性，这里的延时大小不开放出来
            # 一般情况下只要不是`同时`发起的请求都是能够成功的
            # 这里设置少量的延时进一步提高成功率
            time.sleep(0.5)
            return ret
        finally:
            lock.release()

    return inner
