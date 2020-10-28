import time
from threading import Lock

_lock = Lock()


def queued_up(func=None):
    """队列执行函数, 所有被包装的函数共用同一个队列, 该装饰器适用于所有函数"""
    if func is None:
        return queued_up

    def inner(ctx):
        try:
            _lock.acquire()
            ret = func(ctx)
            # 为了易用性，这里的延时大小不开放出来
            # 一般情况下只要不是`同时`发起的请求都是能够成功的
            # 这里设置少量的延时进一步提高成功率
            time.sleep(0.5)
            return ret
        finally:
            _lock.release()

    return inner
