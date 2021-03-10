import functools
import time
from collections import defaultdict
from queue import Queue
from threading import Thread

from botoy.log import logger


class TaskThread(Thread):
    def __init__(self):
        super().__init__()
        self.tasks = Queue(maxsize=-1)
        self.setDaemon(True)
        self.start()

    def run(self):
        while True:
            try:
                self.tasks.get()()
            except Exception as e:
                logger.warning(f'queued_up装饰器: 队列任务出错{e}')
            time.sleep(0.6)

    def put_task(self, target, *args):
        task = functools.partial(target, *args)
        self.tasks.put(task)


taskThread_dict = defaultdict(TaskThread)


def queued_up(func=None, *, name='default'):
    """队列执行函数
    :param name: 指定队列分组, 不同的名称用不同的队列
    """
    if func is None:
        return functools.partial(queued_up, name=name)

    def inner(ctx):
        task_thread = taskThread_dict[repr(name)]
        task_thread.put_task(func, ctx)

    return inner
