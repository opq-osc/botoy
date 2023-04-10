import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from .config import jconfig
from .log import LoguruHandler, logger

# Reference: https://github.com/nonebot/plugin-apscheduler
apscheduler_logger = logging.getLogger("apscheduler")
apscheduler_logger.setLevel(int(jconfig.apscheduler_log_level or 30))
apscheduler_logger.handlers.clear()
apscheduler_logger.addHandler(LoguruHandler())

scheduler = BackgroundScheduler()
async_scheduler = AsyncIOScheduler()


def start_scheduler():
    if not scheduler.running:
        scheduler.configure(
            {
                "apscheduler.timezone": "Asia/Shanghai",
                **(jconfig.apscheduler_config or {}),
            }
        )
        scheduler.start()
        logger.info("同步定时任务已启动")
    if not async_scheduler.running:
        async_scheduler.configure(
            {
                "apscheduler.timezone": "Asia/Shanghai",
                **(jconfig.apscheduler_config or {}),
            }
        )
        async_scheduler.start()
        logger.info("异步定时任务已启动")


if jconfig.apscheduler_autostart is None or jconfig.apscheduler_autostart:
    start_scheduler()

__all__ = ["scheduler", "async_scheduler", "start_scheduler"]
