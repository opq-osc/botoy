# pylint: disable=W0212
import os
import sys

from loguru import logger as _logger

logger = _logger

logger.remove()


def _init(console_log=True, file_log=False):
    """
    :param console_log: 该参数控制控制台日志等级,为True输出INFO等级日志,为False输出EROOR等级的日志
    :param file_log: 该参数控制日志文件开与关,为True输出INFO等级日志的文件,为False关闭输出日志文件

    环境变量``BOTOY_LOG_LEVEL``拥有最高优先级
    """
    BOTOY_LOG_LEVEL = os.getenv('BOTOY_LOG_LEVEL')
    if console_log:
        logger.add(
            sys.stdout,
            format='{level.icon} {time:MM-DD HH:mm:ss} <lvl>{level}\t{message}</lvl>',
            colorize=True,
            level=BOTOY_LOG_LEVEL or 'INFO',
        )
    else:
        logger.add(
            sys.stdout,
            format='{level.icon} {time:MM-DD HH:mm:ss} <lvl>{level}\t{message}</lvl>',
            colorize=True,
            level=BOTOY_LOG_LEVEL or 'ERROR',
        )

    if file_log:
        logger.add(
            './logs/{time}.log',
            format='{time:YYYY-MM-DD HH:mm} {level}\t{message}',
            rotation='1 day',
            encoding='utf-8',
            level=BOTOY_LOG_LEVEL or 'INFO',
        )


logger._init = _init
# 初始化默认值
logger._init()
