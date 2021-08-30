# pylint: disable = too-many-instance-attributes, W0212,W0236,E1133
import asyncio
import copy
import traceback
from typing import Callable, Union

import socketio

from botoy.client import Botoy
from botoy.log import logger
from botoy.model import EventMsg, FriendMsg, GroupMsg


class AsyncBotoy(Botoy):
    def run_in_pool(self, func: Callable, *args):
        self.pool.submit(func, *args)

    async def _context_distributor(self, context: Union[FriendMsg, GroupMsg, EventMsg]):
        if isinstance(context, FriendMsg):
            receivers = [
                *self._friend_msg_receivers,
                *self.plugMgr.friend_msg_receivers,
            ]
        elif isinstance(context, GroupMsg):
            receivers = [
                *self._group_msg_receivers,
                *self.plugMgr.group_msg_receivers,
            ]
        elif isinstance(context, EventMsg):
            receivers = [
                *self._event_receivers,
                *self.plugMgr.event_receivers,
            ]
        else:
            return

        coros = []

        for receiver in receivers:
            new_context = copy.deepcopy(context)
            if asyncio.iscoroutinefunction(receiver):
                coros.append(receiver(new_context))  # type: ignore
            else:
                self.pool.submit(receiver, new_context)

        try:
            await asyncio.gather(*coros)
        except Exception:
            logger.error(traceback.format_exc())

    async def _friend_msg_handler(self, msg):
        context = FriendMsg(msg)
        if self.qq and context.CurrentQQ not in self.qq:
            return
        logger.info(f"{context.__class__.__name__} ->  {context.data}")
        # 黑名单
        if context.FromUin in self.config.friend_blacklist:
            return
        # 屏蔽用户
        if context.FromUin in self.config.blocked_users:
            return
        # 中间件
        if self._friend_context_middlewares:
            for middleware in self._friend_context_middlewares:
                new_context = middleware(context)
                if isinstance(new_context, type(context)):
                    context = new_context
                else:
                    return
        # 传递几个数据供(插件中的)接收函数调用, 其他不再注释
        setattr(context, "_host", self.config.host)
        setattr(context, "_port", self.config.port)
        # return await asyncio.gather(self._context_distributor(context))
        return await self._context_distributor(context)

    async def _group_msg_handler(self, msg):
        context = GroupMsg(msg)
        if self.qq and context.CurrentQQ not in self.qq:
            return
        logger.info(f"{context.__class__.__name__} ->  {context.data}")
        # 黑名单
        if context.FromGroupId in self.config.group_blacklist:
            return
        # 屏蔽用户
        if context.FromUserId in self.config.blocked_users:
            return
        # 中间件
        if self._group_context_middlewares:
            for middleware in self._group_context_middlewares:
                new_context = middleware(context)
                if isinstance(new_context, type(context)):
                    context = new_context
                else:
                    return
        setattr(context, "_host", self.config.host)
        setattr(context, "_port", self.config.port)
        return await self._context_distributor(context)

    async def _event_handler(self, msg):
        context = EventMsg(msg)
        if self.qq and context.CurrentQQ not in self.qq:
            return
        logger.info(f"{context.__class__.__name__} ->  {context.data}")
        # 中间件
        if self._event_context_middlewares:
            for middleware in self._event_context_middlewares:
                new_context = middleware(context)
                if isinstance(new_context, type(context)):
                    context = new_context
                else:
                    return
        setattr(context, "_host", self.config.host)
        setattr(context, "_port", self.config.port)
        return await self._context_distributor(context)

    async def run(self):
        sio = socketio.AsyncClient()
        sio.event(self.connect)
        sio.event(self.disconnect)
        sio.on("OnGroupMsgs")(self._group_msg_handler)  # type: ignore
        sio.on("OnFriendMsgs")(self._friend_msg_handler)  # type: ignore
        sio.on("OnEvents")(self._event_handler)  # type: ignore

        logger.info("Connecting to the server...")

        try:
            await sio.connect(self.config.address, transports=["websocket"])
        except Exception:
            logger.error(traceback.format_exc())
            await sio.disconnect()
            self.pool.shutdown(wait=False)
        else:
            try:
                await sio.wait()
            except KeyboardInterrupt:
                pass
            finally:
                print("bye~")
                await sio.disconnect()
                self.pool.shutdown(wait=False)
