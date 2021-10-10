# pylint: disable = too-many-instance-attributes, W0212,W0236,E1133
import asyncio
import copy
import traceback
from typing import Union

import socketio

from botoy.client import Botoy
from botoy.log import logger
from botoy.model import EventMsg, FriendMsg, GroupMsg


class AsyncBotoy(Botoy):
    def _msg_handler_factory(self, cls):
        async def handler(msg):
            return await self._context_handler(cls(msg))

        return handler

    async def _context_handler(self, context: Union[FriendMsg, GroupMsg, EventMsg]):
        passed_context = self._context_checker(context)
        if passed_context:
            return await self._context_distributor(passed_context)

    async def _context_distributor(self, context: Union[FriendMsg, GroupMsg, EventMsg]):
        coros = []

        for receiver in self._get_context_receivers(context):

            new_context = copy.deepcopy(context)
            if asyncio.iscoroutinefunction(receiver):
                coros.append(receiver(new_context))  # type: ignore
            else:
                self.pool.submit(receiver, new_context)

        try:
            await asyncio.gather(*coros)
        except Exception:
            logger.error(traceback.format_exc())

    async def run(self):
        sio = socketio.AsyncClient()
        sio.event(self.connect)
        sio.event(self.disconnect)
        sio.on("OnGroupMsgs", handler=self._group_msg_handler)
        sio.on("OnFriendMsgs", handler=self._friend_msg_handler)
        sio.on("OnEvents", handler=self._event_handler)

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

    async def run_no_wait(self):
        sio = socketio.AsyncClient()

        sio.event(self.connect)
        sio.event(self.disconnect)
        sio.on("OnGroupMsgs", handler=self._group_msg_handler)
        sio.on("OnFriendMsgs", handler=self._friend_msg_handler)
        sio.on("OnEvents", handler=self._event_handler)

        logger.info("Connecting to the server...")

        try:
            await sio.connect(self.config.address, transports=["websocket"])
        except Exception:
            logger.error(traceback.format_exc())
            await sio.disconnect()
            self.pool.shutdown(wait=False)
