# pylint: disable=W0212
import logging
import os
import sys

from loguru import logger as _logger

logger = _logger

CONSOLE_LOG_FORMAT = "{level.icon} {time:MM-DD HH:mm:ss} <lvl>{level}\t{message}</lvl>"
FILE_LOG_FORMAT = "{time:YYYY-MM-DD HH:mm} {level}\t{message}"
FILE_LOG_PATH_NAMING = "./logs/{time}.log"


def logger_init(console_log=True, file_log=False):
    """
    :param console_log: 该参数控制控制台日志等级,为True输出INFO等级日志,为False输出EROOR等级的日志
    :param file_log: 该参数控制日志文件开与关,为True输出INFO等级日志的文件,为False关闭输出日志文件

    环境变量``BOTOY_LOG_LEVEL``拥有最高优先级
    """
    logger.remove()

    BOTOY_LOG_LEVEL = os.getenv("BOTOY_LOG_LEVEL")
    if console_log:
        logger.add(
            sys.stdout,
            format=CONSOLE_LOG_FORMAT,
            colorize=True,
            level=BOTOY_LOG_LEVEL or "INFO",
        )
    else:
        logger.add(
            sys.stdout,
            format=CONSOLE_LOG_FORMAT,
            colorize=True,
            level=BOTOY_LOG_LEVEL or "ERROR",
        )

    if file_log:
        logger.add(
            FILE_LOG_PATH_NAMING,
            format=FILE_LOG_FORMAT,
            rotation="1 day",
            encoding="utf-8",
            level=BOTOY_LOG_LEVEL or "INFO",
        )


class LoguruHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:  # type: ignore
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


sio_logger = logging.getLogger("socketio.client")
sio_logger.handlers.clear()
sio_logger.addHandler(LoguruHandler())
if sio_logger.level == logging.NOTSET:
    sio_logger.setLevel(logging.INFO)

logger_init()
