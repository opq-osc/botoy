import functools
from collections import defaultdict

from ..pool import WorkerPool


class TaskThread(WorkerPool):
    def __init__(self):
        super().__init__(max_workers=1)

    def put_task(self, target, *args):
        self.submit(target, *args)


task_pool_dict = defaultdict(TaskThread)


def queued_up(func=None, *, name="default"):
    """队列执行函数
    :param name: 指定队列分组, 不同的名称用不同的队列
    """
    if func is None:
        return functools.partial(queued_up, name=name)

    def inner(ctx):
        task_pool_dict[repr(name)].put_task(func, ctx)

    return inner
