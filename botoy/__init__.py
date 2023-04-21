"""
============================================
= Github: https://github.com/opq-osc/botoy =
============================================
"""

from .__version__ import __version__, check_version
from ._internal import contrib as contrib
from ._internal.action import Action as Action
from ._internal.client import Botoy as Botoy
from ._internal.client import mark_recv as mark_recv
from ._internal.config import jconfig as jconfig
from ._internal.context import ctx as ctx
from ._internal.log import logger as logger
from ._internal.schedule import async_scheduler as async_scheduler
from ._internal.schedule import scheduler as scheduler
from ._internal.schedule import start_scheduler as start_scheduler
from ._internal.sugar import S as S

bot = Botoy()
action = Action()

check_version()
del check_version
