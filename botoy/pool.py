import traceback
from concurrent.futures import ThreadPoolExecutor

from botoy.log import logger


class WorkerPool(ThreadPoolExecutor):
    def resize(self, workers: int):
        self._max_workers = workers

    def callback(self, worker):
        worker_exception = worker.exception()
        if worker_exception:
            try:
                raise worker_exception
            except Exception:
                logger.error(traceback.format_exc())

    def submit(self, *args, **kwargs):
        super().submit(*args, **kwargs).add_done_callback(self.callback)
