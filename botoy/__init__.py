"""
============================================
= Github: https://github.com/opq-osc/botoy =
============================================
"""

from .__version__ import __version__, check_version
from ._internal import contrib as contrib

# action
from ._internal.action import Action as Action

# client
from ._internal.client import Botoy as Botoy
from ._internal.client import mark_recv as mark_recv

# config
from ._internal.config import jconfig as jconfig

# context
from ._internal.context import ctx as ctx

# contrib
from ._internal.contrib import Revoker as Revoker
from ._internal.contrib import async_run as async_run
from ._internal.contrib import download as download
from ._internal.contrib import file_to_base64 as file_to_base64
from ._internal.contrib import get_cache_dir as get_cache_dir
from ._internal.contrib import sync_run as sync_run
from ._internal.contrib import to_async as to_async

# log
from ._internal.log import logger as logger

# mahiro
from ._internal.mahiro import Mahiro as Mahiro

# receiver
from ._internal.receiver import start_session as start_session

# schedule
from ._internal.schedule import async_scheduler as async_scheduler
from ._internal.schedule import scheduler as scheduler
from ._internal.schedule import start_scheduler as start_scheduler

# sugar
from ._internal.sugar import S as S

bot = Botoy()
action = Action()

check_version()
del check_version
