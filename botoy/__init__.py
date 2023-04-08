"""
============================================
= Github: https://github.com/opq-osc/botoy =
============================================
"""

from ._internal.client import Botoy as Botoy
from ._internal.client import mark_recv as mark_recv

# from .__version__ import check_version
from ._internal.config import jconfig as jconfig
from ._internal.context import ctx as ctx

bot = Botoy()

# check_version()
# del check_version
