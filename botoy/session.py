import threading
from time import monotonic as time
from time import sleep
from typing import Union

from botoy.model import FriendMsg, GroupMsg


class _SessionState:
    def __init__(self):
        self.state = {}
        self.mutex = threading.Lock()
        self.not_empty = threading.Condition(self.mutex)

    def get(self, key, timeout=None, default=None):
        value = self.pop(key, timeout, default)
        self.set(key, value)
        return value

    def pop(self, key, timeout=None, default=None):
        if timeout is None:
            timeout = 5 * 60
        with self.not_empty:
            endtime = time() + timeout
            while not key in self.state:
                remaining = endtime - time()
                if remaining <= 0.0:
                    return default
                self.not_empty.wait(remaining)
        value = self.state.pop(key)
        return value

    def set(self, key, value):
        with self.mutex:
            self.state[key] = value
            self.not_empty.notify()

    def has(self, key):
        return key in self.state

    def clear(self):
        self.state.clear()


class Session:
    def __init__(self, expire=None):
        self.closed = False
        self.state = _SessionState()
        self.mutex = threading.Lock()
        self.refresh_last_work()
        if expire is None:
            self.expire = 10 * 60
        else:
            self.expire = expire
        self.waiting = False

    @property
    def should_closed(self):
        """是否超过expire时长无任何操作"""
        return time() - self._last_work >= self.expire

    def refresh_last_work(self):
        """重置上一次使用的时间"""
        with self.mutex:
            self._last_work = time()

    def close(self):
        """关闭该session"""
        self.closed = True
        self.state.clear()

    def pop(self, key, timeout=None, default=None):
        """获取键值数据并清除该键值对数据, 该方法会一直阻塞，直到所要获取的数据存在
        :param timeout: 阻塞等待的时间，单位为秒，默认为5分钟
        :param default: 返回的默认值，如果阻塞超过timeout则返回该参数
        """
        self.refresh_last_work()
        with self.mutex:
            self.waiting = True
        value = self.state.pop(key, timeout, default)
        with self.mutex:
            self.waiting = False
        return value

    def get(self, key, timeout=None, default=None):
        """获取键值数据, 该方法会一直阻塞，直到所要获取的数据存在
        :param timeout: 阻塞等待的时间，单位为秒, 默认为5分钟
        :param default: 返回的默认值，如果阻塞超过timeout则返回该参数
        """
        self.refresh_last_work()
        with self.mutex:
            self.waiting = True
        value = self.state.get(key, timeout, default)
        with self.mutex:
            self.waiting = False
        return value

    def set(self, key, value):
        """设置键值对数据，如果键已存在，则更新数据"""
        self.refresh_last_work()
        return self.state.set(key, value)

    def has(self, key) -> bool:
        """如果该键值数据已存在则返回`True`, 反之返回`False`
        :param key: 需要查询的键名
        """
        self.refresh_last_work()
        return self.state.has(key)

    def clear(self):
        """清除session state中的所有数据"""
        self.refresh_last_work()
        self.state.clear()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if not self.waiting:
            self.close()
        return True


class SessionController:
    """会话控制器，每个功能或插件都应该对应唯一的该对象
    :param expire: 如果session无任何操作超过该时长，该session会自动关闭, 单位为秒
    """

    def __init__(self, expire=None):
        self._sessions = {}
        self._mutex = threading.Lock()
        self._expire = expire

        # 每1分钟清理一次无用session
        threading.Thread(target=self._clean_task, daemon=True).start()

    def _clean_task(self):
        while True:
            sleep(60)
            self.clean()

    def clean(self):
        """清理已关闭或应该关闭的session"""
        # print("cleaning")
        with self._mutex:
            self._sessions = {
                session_id_: session_
                for session_id_, session_ in self._sessions.items()
                if not session_.closed and not session_.should_closed
            }
        # print(self._sessions)

    def _pick_up_session(self, session_id) -> Session:
        # 获取需要的session
        if session_id in self._sessions:
            session = self._sessions[session_id]  # type: Session
            if session.closed or session.should_closed:
                session = Session(self._expire)
                self._sessions[session_id] = session
        else:
            session = Session(self._expire)
            self._sessions[session_id] = session
        return session

    def get_session(self, ctx: Union[GroupMsg, FriendMsg], single_user=True) -> Session:
        """获取session
        :param ctx: 该参数类型只能为群消息(GroupMsg), 好友消息(FriendMsg)
        :param single_user: 如果为`True`，则表示该session仅对单个用户有效，如果为`False`,
                            则对同一群组的其他用户都有效。如果是好友消息，该项无需设置，必须为`True`，
                            否则将报错。默认为`True`
        """
        if single_user:
            if isinstance(ctx, GroupMsg):
                session_id = '{}_{}'.format(ctx.FromUserId, ctx.FromGroupId)
            elif isinstance(ctx, FriendMsg):
                session_id = '{}'.format(ctx.FromUin)
            else:
                raise ValueError("'ctx'必须为GroupMsg或FriendMsg类型")
        else:
            if not isinstance(ctx, GroupMsg):
                raise ValueError("'ctx'只能为GroupMsg类型")
            session_id = str(ctx.FromGroupId)
        return self._pick_up_session(session_id)
