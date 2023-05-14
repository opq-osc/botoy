# pylint: disable=R0915
import inspect
import traceback
from typing import Callable, List, NoReturn, Optional, Union

from ..log import logger
from ..model import FriendMsg, GroupMsg
from .base import Session, SessionController
from .globals import _ctx, _session
from .prompt import Prompt

FILTER_SUCCESS = "filter successfully"


class RejectException(Exception):
    pass


class FinishException(Exception):
    pass


class ConditionHandler:
    def __init__(self, keys, target):
        self.keys = keys
        self.target = target
        self.retired = False

    def retire(self):
        self.retired = True

    def work(self):
        self.retired = False


class SessionHandler:
    def __init__(self, *filters, single_user=True, expiration: Optional[int] = None):
        self.filters = list(filters)
        self.single_user = single_user
        self.sc = SessionController(expiration)
        # self.handle
        self.handler = None
        # self.got
        self.condition_handlers: List[ConditionHandler] = []  # 具体操作时要和session绑定
        # self.receive
        self.receiver = None
        # self.parse
        self.parser = None

    def got(self, *keys):
        """注册一个condition_handler

        当session存在所有keys数据时，将被调用。
        函数参数可选，将``keys``中的任意一个作为函数参数名，运行时将自动传入对应值
        """

        def deco(target):
            self.condition_handlers.append(ConditionHandler(keys, target))

        return deco

    def parse(self, parser):
        """注册parser, 参数为新消息ctx

        session 开启后，自动设置给等待数据的值为parser的返回值"""
        self.parser = parser

    def receive(self, receiver):
        """注册receiver, 无参数

        session 开启后，每次接收到新消息都会运行该函数
        """
        self.receiver = receiver

    def handle(self, handler):
        """注册handler, 无参数

        在 session 被新建后运行, 并且在 session 存在期间只会运行一次
        """
        self.handler = handler

    def message_receiver(self, msg_ctx: Union[GroupMsg, FriendMsg]):
        """消息接收函数"""
        # 过滤机器人自身消息
        if msg_ctx.CurrentQQ == (
            msg_ctx.FromUserId if isinstance(msg_ctx, GroupMsg) else msg_ctx.FromUin
        ):
            return

        # 如果session存在，则需要对该消息进行各种操作
        if self.sc.session_existed(msg_ctx, self.single_user):
            session = self.sc.get_session(msg_ctx, self.single_user)  # type: ignore
            logger.debug(f"存在session => {session}")
            _ctx.set(msg_ctx)
            _session.set(session)
            # 1. 执行receiver
            if self.receiver is not None:
                logger.debug("执行receiver")
                self.receiver()
            # 2. 自动设置session数据
            if session.waitings:
                if self.parser is None:
                    data = msg_ctx.Content
                else:
                    data = self.parser(msg_ctx)
                logger.debug(f"有正在等待的数据，开始自动设置 {session.waitings[0]} => {data}")
                session.set(session.waitings[0], data)
            # 3. 执行condition handler
            logger.debug("checking condition handler")
            if not hasattr(session, "_condition_handlers"):
                setattr(session, "_condition_handlers", self.condition_handlers.copy())
            for c_h in [
                c_h
                for c_h in getattr(session, "_condition_handlers")
                if not c_h.retired
            ]:  # type: ConditionHandler
                for need_key in c_h.keys:
                    if not session.has(need_key):
                        break
                else:
                    logger.debug(f"running condition handler {c_h}")
                    try:
                        c_h.retire()
                        ###########
                        c_h.target(
                            **{
                                key: session.get(key)
                                for key in c_h.keys
                                if key in inspect.signature(c_h.target).parameters
                                and session.has(key)
                            }
                        )
                    except RejectException:  # 设置为获取新数据后再次运行
                        for need_key in c_h.keys:
                            session.remove(need_key)
                        c_h.work()
                    except FinishException:
                        pass
            return

        # session不存在，判断是否需要新建session
        filters = self.filters.copy()
        ret = FILTER_SUCCESS
        if filters:
            try:
                ret = filters[0](lambda _: FILTER_SUCCESS)(msg_ctx)
            except AttributeError:
                ret = filters[0](msg_ctx)
            del filters[0]
        for filter in filters:
            try:
                ret = filter(lambda _: ret)(msg_ctx)
            except AttributeError:
                ret = filter(msg_ctx)
            if ret != FILTER_SUCCESS:
                break

        # 新建session
        # 过滤成功表示符合创建sesion条件
        # 当且仅当新建session就开始运行handler，直到handler退出
        if ret == FILTER_SUCCESS and not self.sc.session_existed(
            msg_ctx, self.single_user
        ):
            session: Session = self.sc.get_session(  # type:ignore
                msg_ctx, self.single_user
            )
            logger.debug(f"新建session => {session}")
            _ctx.set(msg_ctx)
            _session.set(session)
            try:
                if self.handler is not None:
                    self.handler()
            except (RejectException, FinishException):
                session.close()

    def reject(
        self, prompt: Optional[Union[str, Prompt, Callable]] = None, **kwargs
    ) -> NoReturn:
        """该方法调用对应session的resolve_prompt方法
        :param prompt: 如果是字符串类型，则发送文字消息；如果是Prompt类型，则发送相应消息；
                        如果是函数(Callable), 则会直接调用，并将额外命名参数传入该函数
        :param kwargs: 如果prompt是函数类型，该参数将传递给prompt运行
        """
        try:
            _session.get().resolve_prompt(prompt, **kwargs)
        except Exception:
            logger.error(traceback.format_exc())
        finally:
            raise RejectException

    def finish(
        self, prompt: Optional[Union[str, Prompt, Callable]] = None, **kwargs
    ) -> NoReturn:
        """该方法调用对应session的resolve_prompt方法
        :param prompt: 如果是字符串类型，则发送文字消息；如果是Prompt类型，则发送相应消息；
                        如果是函数(Callable), 则会直接调用，并将额外命名参数传入该函数
        :param kwargs: 如果prompt是函数类型，该参数将传递给prompt运行
        """
        try:
            _session.get().resolve_prompt(prompt, **kwargs)
        except Exception:
            logger.error(traceback.format_exc())
        finally:
            raise FinishException

    def receive_group_msg(self) -> "SessionHandler":
        """接收该插件的群消息"""
        inspect.currentframe().f_back.f_globals.update(  # type: ignore
            receive_group_msg=self.message_receiver
        )
        return self

    def receive_friend_msg(self) -> "SessionHandler":
        """接收该插件的好友消息"""
        inspect.currentframe().f_back.f_globals.update(  # type: ignore
            receive_friend_msg=self.message_receiver
        )
        return self
