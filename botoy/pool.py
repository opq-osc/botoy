# 参考
# https://github.com/ydf0509/threadpool_executor_shrink_able/blob/master/threadpool_executor_shrink_able/sharp_threadpoolexecutor.py
# https://github.com/GoodManWEN/ThreadPoolExecutorPlus/blob/main/ThreadPoolExecutorPlus/thread.py
# https://github.com/python/cpython/blob/main/Lib/concurrent/futures/thread.py
# 修改并简化了部分内容，因为不想为了框架需要再继承一遍
# 如果使用有问题再考虑直接引用库
import atexit
import os
import queue
import threading
import traceback
import weakref
from concurrent import futures
from typing import Optional

from .log import logger

_thread_queue = weakref.WeakKeyDictionary()
_exit = False


@atexit.register
def _():
    global _exit
    _exit = True
    for q in _thread_queue.values():
        q.put(None)
    for t in _thread_queue.keys():
        t.join()


class Worker:
    def __init__(self, future: futures.Future, func, args, kwargs):
        self.future = future
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        if not self.future.set_running_or_notify_cancel():
            return
        try:
            ret = self.func(*self.args, **self.kwargs)
        except Exception as e:
            logger.error(traceback.format_exc())
            self.future.set_exception(e)
            self = None
        else:
            self.future.set_result(ret)


class WorkerThread(threading.Thread):
    def __init__(self, executor: "WorkerExecutor"):
        super().__init__()
        self.executor: "WorkerExecutor" = executor

    def run(self):
        self.executor._adjust_free_threads(1)
        while True:
            # break/return出死循环即关闭线程
            try:
                worker: Worker = self.executor._worker_queue.get(
                    block=True, timeout=self.executor._keep_alive_time
                )
            except queue.Empty:
                if self.executor._free_threads < self.executor._min_workers:
                    continue
                # 因为是弱引用，这里应该不是必要的
                self.executor._adjust_free_threads(-1)
                self.executor._worker_threads.remove(self)
                _thread_queue.pop(self)
                break

            if worker is not None:
                self.executor._adjust_free_threads(-1)
                worker.run()
                del worker
                self.executor._adjust_free_threads(1)
                continue

            if _exit or self.executor._shutdown:
                self.executor._worker_queue.put(None)
                break


class WorkerExecutor(futures.Executor):
    def __init__(self, max_workers: Optional[int] = None):
        max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        if max_workers <= 0:
            raise ValueError("max_workers must be greater than 0")
        self._max_workers = max_workers
        self._min_workers = 5  # 允许的空闲线程数
        self._keep_alive_time = 60  # 空闲线程存活时间

        self._worker_queue = queue.Queue()
        self._worker_threads = weakref.WeakSet()

        self._shutdown = False
        self._shutdown_lock = threading.RLock()

        self._free_threads = 0
        self._free_threads_lock = threading.RLock()

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown = True
            self._worker_queue.put(None)
        if wait:
            for t in self._worker_threads:
                t.join()

    def submit(self, target, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError("工作池已关闭，无法添加新任务")
            if _exit:
                raise RuntimeError("程序已退出，无法添加新任务")

            future = futures.Future()
            worker = Worker(future, target, args, kwargs)

            self._worker_queue.put(worker)

            self._schedule_threads()
            return future

    def _schedule_threads(self):
        # 如果有空闲线程并且未超过限制数目，不管是否达到最大线程数都不需要创建新线程
        if (
            len(self._worker_threads) < self._max_workers
            and self._free_threads < self._min_workers
        ):
            thread = WorkerThread(self)  # use executor reference??
            thread.setDaemon(True)
            thread.start()

            self._worker_threads.add(thread)
            _thread_queue[thread] = self._worker_queue

    def _adjust_free_threads(self, amount: int):
        with self._free_threads_lock:
            self._free_threads += amount

    submit.__doc__ = futures.Executor.submit.__doc__
    shutdown.__doc__ = futures.Executor.shutdown.__doc__


WorkerPool = WorkerExecutor
