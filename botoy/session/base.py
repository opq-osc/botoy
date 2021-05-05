import functools
import threading
import time
from typing import Any, List, Optional, Union

from botoy.action import Action
from botoy.model import FriendMsg, GroupMsg

DEFAULT_TIMEOUT = 5 * 60
DEFAULT_EXPIRATION = 10 * 60


class SessionBase:
    """会话对象
    :param expiration: 持续无任何操作自动过期关闭时间
    """

    def __init__(self, expiration: int = None):
        self._state = {}
        self._mutex = threading.Lock()
        self._not_empty = threading.Condition(self._mutex)
        self._waitings = []
        self._last_work = time.monotonic()
        self._expiration = expiration or DEFAULT_EXPIRATION

    def get(self, key: str, wait: bool = True, timeout: int = None, default=None):
        """获取数据, 该函数会等待至取到数据或超时，返回默认值
        :param key: 数据键名
        :param timeout: 等待的时间
        :param default: 超时返回的默认值
        """
        self._last_work = time.monotonic()
        if wait:
            try:
                self._not_empty.acquire()
                self.wait_for(key)
                endtime = time.monotonic() + (timeout or DEFAULT_TIMEOUT)
                while not key in self._state:
                    remaining = endtime - time.monotonic()
                    if remaining <= 0.0:
                        return default
                    self._not_empty.wait(remaining)
                return self._state.get(key)
            finally:
                self.do_not_wait(key)
                self._not_empty.release()
        else:
            return self._state.get(key, default=default)

    def pop(self, key: str, wait: bool = True, timeout: int = None, default=None):
        """获取数据,然后删除, 该函数会等待至取到数据或超时，返回默认值
        :param key: 数据键名
        :param timeout: 等待的时间
        :param default: 超时返回的默认值
        """
        self._last_work = time.monotonic()
        value = self.get(key, wait, timeout, default)
        self.remove(key)
        return value

    def set(self, key, value):
        """设置数据
        :param key: 键名
        :param value: 数据
        """
        self._last_work = time.monotonic()
        with self._not_empty:
            self._state[key] = value
            self.do_not_wait(key)
            self._not_empty.notify()

    def has(self, key) -> bool:
        """判断是否存在数据
        :param key: 数据键名
        """
        self._last_work = time.monotonic()
        return key in self._state

    def remove(self, key):
        """删除数据
        :param key: 数据键名
        """
        self._last_work = time.monotonic()
        if key in self._state:
            del self._state[key]

    def clear(self):
        """清空数据"""
        self._last_work = time.monotonic()
        self._state.clear()

    @property
    def waitings(self) -> List[str]:
        '''正在等待的数据'''
        return self._waitings

    def waiting(self, key=None) -> bool:
        """判断是否在等待某项数据, 当使用get_and_wait方法时，所需数据的键名会自动保存直到方法结束等待
        :param key: 需要判断是否在等待该键名的数据, 如果不设置, 则只要存在正在等待的数据，就会返回True
        """
        self._last_work = time.monotonic()
        if key is None:
            return bool(self._waitings)
        return key in self._waitings

    def wait_for(self, key):
        '''手动增加需要等待的数据'''
        self._last_work = time.monotonic()
        if not self.waiting(key):
            self._waitings.append(key)

    def do_not_wait(self, key):
        '''手动删除正在等待的数据'''
        # FIXME: _waitings 使用集合则无序，使用列表可能会同一个数据多次添加
        # 多次添加的需求可能存在，但是此时remove会清除所有的数据
        self._last_work = time.monotonic()
        if key in self._waitings:
            self._waitings.remove(key)

    @property
    def empty(self):
        '''session数据是否为空'''
        return bool(self._state)

    def close(self):
        """关闭该Session
        Session的关闭只是一个标志，即使被关闭，Session的其他方法依然能使用
        """
        self._last_work = float('-inf')

    @property
    def closed(self) -> bool:
        """获取Session关闭状态"""
        return (time.monotonic() - self._last_work) >= self._expiration

    def __repr__(self):
        return f'Session@{self._state}'


class Session(SessionBase):
    def __init__(self, ctx: Union[FriendMsg, GroupMsg], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctx = ctx
        self.action = Action(ctx.CurrentQQ, host=ctx._host, port=ctx._port)

    def send_text(self, text: str):
        if isinstance(self.ctx, FriendMsg):
            return self.action.sendFriendText(self.ctx.FromUin, text)
        return self.action.sendGroupText(self.ctx.FromGroupId, text)

    def send_pic(self, url: str = "", base64: str = "", md5: str = "", text: str = ""):
        if isinstance(self.ctx, FriendMsg):
            return self.action.sendFriendPic(
                self.ctx.FromUin,
                picUrl=url,
                picBase64Buf=base64,
                fileMd5=md5,
                content=text,
            )
        return self.action.sendGroupPic(
            self.ctx.FromGroupId,
            picUrl=url,
            picBase64Buf=base64,
            fileMd5=md5,
            content=text,
        )

    def want(
        self,
        key,
        prompt=None,
        timeout: int = None,
        default: Any = None,
    ):
        if prompt is not None:
            if isinstance(prompt, str):
                self.send_text(prompt)
            else:
                # TODO: catch exceptions
                prompt(self.ctx)
        return self.get(key, wait=True, timeout=timeout, default=default)


class SessionController:
    def __init__(self, session_expiration: int = None):
        self._session_expiration = session_expiration
        self._session_storage = {}

    @property
    def session_storage(self) -> dict:
        '''返回所有未关闭的session'''
        self._session_storage = {
            sid: s for sid, s in self._session_storage.items() if not s.closed
        }
        return self._session_storage

    def define_session_id(
        self, ctx: Union[GroupMsg, FriendMsg], single_user=True
    ) -> str:
        """定义session id
        :param single_user: 该session是否仅对单个用户有效，群聊内设置为False则表示任何人的对话都作用于该session
        """
        if isinstance(ctx, GroupMsg):
            if single_user:
                sid = '{group_id}-{user_id}'.format(
                    group_id=ctx.FromGroupId, user_id=ctx.FromUserId
                )
            else:
                sid = str(ctx.FromGroupId)
        elif isinstance(ctx, FriendMsg):
            sid = ctx.FromUin
        else:
            raise ValueError('Type of ctx must be GroupMsg or FriendMsg.')
        return sid

    def remove_session(self, ctx: Union[FriendMsg, GroupMsg], single_user: bool = True):
        sid = self.define_session_id(ctx, single_user)
        if sid in self.session_storage:
            self.session_storage.remove(sid)

    def session_existed(
        self, ctx: Union[FriendMsg, GroupMsg], single_user: bool = True
    ):
        sid = self.define_session_id(ctx, single_user)
        return sid in self.session_storage

    def get_session(
        self,
        ctx: Union[GroupMsg, FriendMsg],
        single_user: bool = True,
        create: bool = True,
    ) -> Optional[Session]:
        sid = self.define_session_id(ctx, single_user)
        if sid in self.session_storage:
            return self.session_storage[sid]
        if create:
            s = Session(ctx, self._session_expiration)
            self.session_storage[sid] = s
            return s
        return None

    def __repr__(self):
        return f'SessionController@{self.session_storage}'
