"""一些用于接收函数的装饰器（用于异步）"""
from ._common_text import common_text
from ._ensure_tempMsg import ensure_tempMsg
from ._equal_content import equal_content
from ._from_botself import from_botself
from ._from_phone import from_phone
from ._from_these_groups import from_these_groups
from ._from_these_users import from_these_users
from ._ignore_botself import ignore_botself
from ._ignore_tempMsg import ignore_tempMsg
from ._ignore_these_groups import ignore_these_groups
from ._ignore_these_users import ignore_these_users
from ._in_content import in_content
from ._need_action import need_action
from ._on_regexp import on_regexp
from ._re_findall import re_findall
from ._re_match import re_match
from ._startswith import startswith
from ._these_msgtypes import these_msgtypes

__all__ = [
    "ensure_tempMsg",
    "equal_content",
    "from_phone",
    "from_these_groups",
    "from_these_users",
    "from_botself",
    "ignore_botself",
    "ignore_tempMsg",
    "ignore_these_users",
    "ignore_these_groups",
    "in_content",
    "on_regexp",
    "startswith",
    "these_msgtypes",
    "common_text",
    "need_action",
    "re_findall",
    "re_match",
]
