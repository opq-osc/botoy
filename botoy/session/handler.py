# pylint: disable=R0915
import inspect
from typing import Union

from botoy.log import logger
from botoy.model import FriendMsg, GroupMsg

from .base import Session, SessionController
from .globals import _ctx, _session

FILTER_SUCCESS = 'filter successfully'


class RejectException(Exception):
    pass


class FinishException(Exception):
    pass


class ConditionHandler:
    def __init__(self, keys, prompt, target):
        self.keys = keys
        self.prompt = prompt
        self.target = target
        self.retired = False

    def retire(self):
        self.retired = True

    def work(self):
        self.retired = False


class SessionHandler:
    def __init__(self, *filters, single_user=True, expiration: int = None):
        self.filters = list(filters)
        self.single_user = single_user
        self.sc = SessionController(expiration)
        # self.handle
        self.handler = None
        # self.got
        self.condition_handlers = []  # 具体操作时要和session绑定
        # self.receive
        self.receiver = None
        # self.parse
        self.parser = None

    def got(self, *keys, prompt=None):
        def deco(target):
            self.condition_handlers.append(ConditionHandler(keys, prompt, target))

        return deco

    def parse(self, parser):
        self.parser = parser

    def receive(self, receiver):
        self.receiver = receiver

    def handle(self, handler):
        self.handler = handler

    def message_receiver(self, msg_ctx: Union[GroupMsg, FriendMsg]):
        # 过滤机器人自身消息
        if msg_ctx.CurrentQQ == (
            msg_ctx.FromUserId if isinstance(msg_ctx, GroupMsg) else msg_ctx.FromUin
        ):
            logger.debug('忽略自身消息')
            return
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
        if ret == FILTER_SUCCESS:
            if not self.sc.session_existed(msg_ctx, self.single_user):
                session: Session = self.sc.get_session(msg_ctx, self.single_user)
                logger.debug(f'新建session => {session}')
                _ctx.set(msg_ctx)
                _session.set(session)
                try:
                    self.handler()
                except (RejectException, FinishException):
                    session.close()
                return

        # 如果session存在，则需要对该消息进行各种操作
        if self.sc.session_existed(msg_ctx, self.single_user):
            session = self.sc.get_session(msg_ctx, self.single_user)
            logger.debug(f'存在session => {session}')
            _ctx.set(msg_ctx)
            _session.set(session)
            # 1. 执行receiver
            if self.receiver is not None:
                logger.debug('执行receiver')
                self.receiver()
            # 2. 自动设置session数据
            if session.waitings:
                if self.parser is None:
                    data = msg_ctx.Content
                else:
                    data = self.parser(data)
                logger.debug(f'有正在等待的数据，开始自动设置 {session.waitings[0]} => {data}')
                session.set(session.waitings[0], data)
            # 3. 执行condition handler
            logger.debug('checking condition handler')
            if not hasattr(session, '_condition_handlers'):
                setattr(session, '_condition_handlers', self.condition_handlers.copy())
            for c_h in [
                c_h
                for c_h in getattr(session, '_condition_handlers')
                if not c_h.retired
            ]:  # type: ConditionHandler
                for need_key in c_h.keys:
                    if not session.has(need_key):
                        break
                else:
                    # TODO
                    # 处理prompt
                    logger.debug(f'running condition handler {c_h}')
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
                        c_h.rework()
                    except FinishException:
                        pass

    def reject(self):
        raise RejectException

    def finish(self):
        raise FinishException

    def receive_group_msg(self):
        inspect.currentframe().f_back.f_globals.update(
            receive_group_msg=self.message_receiver
        )
        return self

    def receive_friend_msg(self):
        inspect.currentframe().f_back.f_globals.update(
            receive_friend_msg=self.message_receiver
        )
        return self
