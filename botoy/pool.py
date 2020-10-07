from concurrent.futures import ThreadPoolExecutor

from botoy.exceptions import ThreadPoolError
from botoy.log import logger


class WorkerPool(ThreadPoolExecutor):
    def resize(self, workers: int):
        self._max_workers = workers

    def callback(self, worker):
        worker_exception = worker.exception()
        if worker_exception:
            logger.exception(ThreadPoolError(worker_exception))

    def submit(self, *args, **kwargs):
        super().submit(*args, **kwargs).add_done_callback(self.callback)
