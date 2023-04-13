import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union
from uuid import uuid4

from ..action import Action
from ..log import logger
from ..model import FriendMsg, GroupMsg
from .prompt import Prompt

DEFAULT_TIMEOUT = 5 * 60
DEFAULT_EXPIRATION = 10 * 60


T = TypeVar("T")


class SessionBase:
    """会话对象
    :param expiration: 持续无任何操作自动过期关闭时间
    """

    def __init__(self, expiration: Optional[int] = None):
        self._state: Dict[str, Any] = {}
        self._mutex = threading.Lock()
        self._not_empty = threading.Condition(self._mutex)
        self._waitings: List[str] = []
        self._last_work = time.monotonic()
        self._expiration = expiration or DEFAULT_EXPIRATION

    def get(
        self, key: str, wait: bool = True, timeout: Optional[int] = None, default=None
    ) -> Any:
        """获取数据, 该函数会等待至取到数据或超时，返回默认值
        :param key: 数据键名
        :param wait: 是否阻塞等待
        :param timeout: 等待的时间
        :param default: 返回的默认值
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
            return self._state.get(key, default)

    def pop(
        self, key: str, wait: bool = True, timeout: Optional[int] = None, default=None
    ) -> Any:
        """获取数据,然后删除, 该函数会等待至取到数据或超时，返回默认值
        :param key: 数据键名
        :param wait: 是否阻塞等待
        :param timeout: 等待的时间
        :param default: 返回的默认值
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
        """正在等待的数据"""
        return self._waitings

    def waiting(self, key=None) -> bool:
        """判断是否在等待某项数据
        :param key: 需要判断是否在等待该键名的数据, 如果不设置, 则只要存在正在等待的数据，就会返回True
        """
        self._last_work = time.monotonic()
        if key is None:
            return bool(self._waitings)
        return key in self._waitings

    def wait_for(self, key):
        """手动增加需要等待的数据"""
        self._last_work = time.monotonic()
        if not self.waiting(key):
            self._waitings.append(key)

    def do_not_wait(self, key):
        """手动删除正在等待的数据"""
        # FIXME: _waitings 使用集合则无序，使用列表可能会同一个数据多次添加
        # 多次添加的需求可能存在，但是此时remove会清除所有的数据
        self._last_work = time.monotonic()
        if key in self._waitings:
            self._waitings.remove(key)

    @property
    def empty(self) -> bool:
        """是否为空"""
        return bool(self._state)

    def close(self):
        """关闭该Session
        Session的关闭只是一个标志，即使被关闭，Session的其他方法依然能使用
        """
        self._last_work = float("-inf")

    @property
    def closed(self) -> bool:
        """获取Session关闭状态"""
        return (time.monotonic() - self._last_work) >= self._expiration

    def __repr__(self):
        return f"Session@{self._state}"


class Session(SessionBase):
    def __init__(self, ctx: Union[FriendMsg, GroupMsg], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctx = ctx
        self.action = Action(
            ctx.CurrentQQ, host=ctx._host, port=ctx._port  # type:ignore
        )

    def send(self, method: str, *args, **kwargs):
        """调用与session对应的action的方法

        该方法会将命名参数中所有值为 '[user]' 和 '[group]'
        分别替换成该session对应的 user_id 和 group_id

        :param method: 方法名
        :param args: 该方法可设置的位置参数
        :param kwargs: 该方法可设置的命名参数
        """
        if isinstance(self.ctx, FriendMsg):
            user = self.ctx.FromUin
            group = self.ctx.TempUin or 0
        else:
            user = self.ctx.FromUserId
            group = self.ctx.FromGroupId
        for k, v in kwargs.copy().items():
            if v == "[user]":
                kwargs[k] = user
            if v == "[group]":
                kwargs[k] = group
        return getattr(self.action, method)(*args, **kwargs)

    def send_text(self, text: str):
        """发送session文字消息
        :param text: 文字内容
        """
        if isinstance(self.ctx, FriendMsg):
            return self.action.sendFriendText(self.ctx.FromUin, text)
        return self.action.sendGroupText(self.ctx.FromGroupId, text)

    def send_pic(
        self, url: str = "", base64: str = "", md5s: List[str] = [], text: str = ""
    ):
        """发送session图片消息
        :param url: 图片URL
        :param base64: 图片base64
        :param md5s: 图片MD5
        :param text: 图片附带文字
        """
        if isinstance(self.ctx, FriendMsg):
            return self.action.sendFriendPic(
                self.ctx.FromUin,
                picUrl=url,
                picBase64Buf=base64,
                picMd5s=md5s,
                content=text,
            )
        return self.action.sendGroupPic(
            self.ctx.FromGroupId,
            picUrl=url,
            picBase64Buf=base64,
            picMd5s=md5s,
            content=text,
        )

    def resolve_prompt(
        self, prompt: Optional[Union[str, Prompt, Callable]] = None, **kwargs
    ):
        """用于统一处理prompt参数
        :param prompt: 如果是字符串类型，则发送文字消息；如果是Prompt类型，则发送相应消息；
                        如果是函数(Callable), 则会直接调用，并将额外命名参数传入该函数
        :param kwargs: 如果prompt是函数类型，该参数将传递给prompt运行
        """
        if prompt is None:
            return None
        elif isinstance(prompt, str):
            return self.send_text(prompt)
        elif isinstance(prompt, Prompt):
            return self.send(prompt.method, *prompt.args, **prompt.kwargs)
        elif callable(prompt):
            return prompt(**kwargs)
        else:
            logger.warning(f"Unknown prompt! => {prompt}")
        return None

    def want(
        self,
        key,
        prompt: Optional[Union[str, Prompt, Callable]] = None,
        pop: bool = False,
        timeout: Optional[int] = None,
        default: Any = None,
        **kwargs,
    ) -> Any:
        """包装get和pop方法，增加prompt参数, 该方法一定会阻塞等待数据
        :param key: 需要的数据键名
        :param prompt: 如果是字符串类型，则发送文字消息；如果是Prompt类型，则发送相应消息；
                        如果是函数(Callable), 则会直接调用，并将额外命名参数传入该函数
        :param pop: 如果为``True``, 则调用pop方法，默认为``False``,使用get方法
        :param timeout: 等待的时间
        :param default: 等待超时返回该默认值
        :param kwargs: 如果prompt是函数类型，该参数将传递给prompt运行
        """
        self.resolve_prompt(prompt=prompt, **kwargs)
        if pop:
            return self.pop(key, wait=True, timeout=timeout, default=default)
        return self.get(key, wait=True, timeout=timeout, default=default)

    def choose(
        self,
        candidates: List[T],
        retry_times: int = 1,
        key: Optional[Callable[[T], Any]] = None,
        always_prompt: bool = True,
        timeout: int = 30,
    ) -> Optional[Tuple[T, int]]:
        """提示用户发送序号选择列表中的一项,
        返回值是一个元组，第一项为选择项，第二项为选择项的索引. 超过重试次数或超时，返回None

        :param candidates: 选项列表
        :param retry_times: 获取重试次数
        :param key: 一个函数，参数为候选列表中项，返回的值将用于发送给用户的提示信息, 默认为`str`
        :param always_prompt: 重试时是否再次发送提示
        :param timeout: 单次获取等待超时时间(秒)
        """
        key = key or str
        items = (key(candidate) for candidate in candidates)
        msg = f"发送对应序号选择一项({retry_times}次机会, 每次你都只有{timeout}秒的选择时间)\n" + "\n".join(
            [f"【{idx}】 {item}" for idx, item in enumerate(items, 1)]
        )
        self.send_text(msg)

        count = 0
        while count < retry_times:
            count += 1
            if count == 1:
                prompt = None
            else:
                prompt = msg if always_prompt else None

            what: str = self.want(str(uuid4()), prompt, pop=True, timeout=timeout)
            if what is None:
                return
            try:
                idx = int(what) - 1
                assert idx >= 0
                return candidates[idx], idx
            except Exception:
                self.send_text("序号错误")


class SessionController:
    def __init__(self, session_expiration: Optional[int] = None):
        self._session_expiration = session_expiration
        self._session_storage: Dict[str, Session] = {}

    @property
    def session_storage(self) -> Dict[str, Session]:
        """返回所有未关闭的session"""
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
                sid = "{group_id}-{user_id}".format(
                    group_id=ctx.FromGroupId, user_id=ctx.FromUserId
                )
            else:
                sid = str(ctx.FromGroupId)
        elif isinstance(ctx, FriendMsg):
            sid = str(ctx.FromUin)
        else:
            raise ValueError("Type of ctx must be GroupMsg or FriendMsg.")
        return sid

    def remove_session(self, ctx: Union[FriendMsg, GroupMsg], single_user: bool = True):
        """移除对应session"""
        sid = self.define_session_id(ctx, single_user)
        if sid in self.session_storage:
            del self.session_storage[sid]

    def session_existed(
        self, ctx: Union[FriendMsg, GroupMsg], single_user: bool = True
    ):
        """判断对应session是否存在"""
        sid = self.define_session_id(ctx, single_user)
        return sid in self.session_storage

    def get_session(
        self,
        ctx: Union[GroupMsg, FriendMsg],
        single_user: bool = True,
        create: bool = True,
    ) -> Optional[Session]:
        """获取session
        :param create: ``True``表示session不存在时，则新建
        """
        sid = self.define_session_id(ctx, single_user)
        if sid in self.session_storage:
            return self.session_storage[sid]
        if create:
            s = Session(ctx, self._session_expiration)
            self.session_storage[sid] = s
            return s
        return None

    def __repr__(self):
        return f"SessionController@{self.session_storage}"
