import sys

from loguru import logger

logger.remove()

logger.add(
    sys.stdout,
    format='{level.icon} {time:YYYY-MM-DD HH:mm:ss} <lvl>{level}\t{message}</lvl>',
    colorize=True,
)


def enble_log_file():
    logger.add(
        './logs/{time}.log',
        format='{time:YYYY-MM-DD HH:mm} {level}\t{message}',
        rotation='1 day',
        encoding='utf-8',
    )
