# pylint: disable=W0236,E1133
import asyncio
import copy
import sys
import traceback
from typing import Callable

import socketio

from botoy.client import Botoy
from botoy.log import logger
from botoy.model import EventMsg, FriendMsg, GroupMsg


class AsyncBotoy(Botoy):
    def _initialize_socketio(self):
        self.socketio = socketio.AsyncClient()
        self.socketio.event()(self.connect)
        self.socketio.event()(self.disconnect)

    def asyncRun(self, func: Callable, *args):
        self.pool.submit(func, *args)

    async def close(self, status=0):
        await self.socketio.disconnect()
        self.pool.shutdown(wait=False)
        self._exit = True
        sys.exit(status)

    async def run(self):
        try:
            await self.socketio.connect(self.config.address, transports=['websocket'])
        except Exception:
            logger.error(traceback.format_exc())
            await self.close(1)
        else:
            try:
                await self.socketio.wait()
            finally:
                print('bye~')
                await self.close(0)

    ########################################################################
    # context distributor
    ########################################################################
    async def _friend_context_distributor(self, context: FriendMsg):
        for f_receiver in [
            *self._friend_msg_receivers,
            *self.plugMgr.friend_msg_receivers,
        ]:
            new_context = copy.deepcopy(context)
            if asyncio.iscoroutinefunction(f_receiver):
                await f_receiver(new_context)
            else:
                self.asyncRun(f_receiver, new_context)

    async def _group_context_distributor(self, context: GroupMsg):
        for g_receiver in [
            *self._group_msg_receivers,
            *self.plugMgr.group_msg_receivers,
        ]:
            new_context = copy.deepcopy(context)
            if asyncio.iscoroutinefunction(g_receiver):
                await g_receiver(new_context)
            else:
                print('==========不是异步=========')
                self.asyncRun(g_receiver, new_context)

    async def _event_context_distributor(self, context: EventMsg):
        for e_receiver in [
            *self._event_receivers,
            *self.plugMgr.event_receivers,
        ]:
            new_context = copy.deepcopy(context)
            if asyncio.iscoroutinefunction(e_receiver):
                await e_receiver(new_context)
            else:
                self.asyncRun(e_receiver, new_context)

    ########################################################################
    # message handler
    ########################################################################
    async def _friend_msg_handler(self, msg):
        context = FriendMsg(msg)
        if self.qq and context.CurrentQQ not in self.qq:
            return
        logger.info(f'{context.__class__.__name__} ->  {context.data}')
        # 黑名单
        if context.FromUin in self.config.friend_blacklist:
            return
        # 屏蔽用户
        if context.FromUin in self.config.blocked_users:
            return
        # 中间件
        if self._friend_context_middlewares:
            for middleware in self._friend_context_middlewares:
                if asyncio.iscoroutinefunction(middleware):
                    new_context = await middleware(context)
                else:
                    new_context = middleware(context)
                if isinstance(new_context, type(context)):
                    context = new_context
                else:
                    return
        await self._friend_context_distributor(context)

    async def _group_msg_handler(self, msg):
        context = GroupMsg(msg)
        if self.qq and context.CurrentQQ not in self.qq:
            return
        logger.info(f'{context.__class__.__name__} ->  {context.data}')
        # 黑名单
        if context.FromGroupId in self.config.group_blacklist:
            return
        # 屏蔽用户
        if context.FromUserId in self.config.blocked_users:
            return
        # 中间件
        if self._group_context_middlewares:
            for middleware in self._group_context_middlewares:
                if asyncio.iscoroutinefunction(middleware):
                    new_context = await middleware(context)
                else:
                    new_context = middleware(context)
                if isinstance(new_context, type(context)):
                    context = new_context
                else:
                    return
        await self._group_context_distributor(context)

    async def _event_handler(self, msg):
        context = EventMsg(msg)
        if self.qq and context.CurrentQQ not in self.qq:
            return
        logger.info(f'{context.__class__.__name__} ->  {context.data}')
        # 中间件
        if self._event_context_middlewares:
            for middleware in self._event_context_middlewares:
                if asyncio.iscoroutinefunction(middleware):
                    new_context = await middleware(context)
                else:
                    new_context = middleware(context)
                if isinstance(new_context, type(context)):
                    context = new_context
                else:
                    return
        await self._event_context_distributor(context)

    ########################################################################
    def __repr__(self):
        return 'Botoy <{}> <host-{}> <port-{}> <address-{}>'.format(
            " ".join([str(i) for i in self.qq]),
            self.config.host,
            self.config.port,
            self.config.address,
        )
