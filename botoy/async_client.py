# pylint: disable = too-many-instance-attributes, W0212,W0236,E1133
import asyncio
import copy
import random
import traceback
from typing import Union

import socketio
from socketio.exceptions import ConnectionError as SioConnectionError

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

    async def run(self, wait: bool = True, sio: socketio.AsyncClient = None):
        """运行
        :param wait: 是否阻塞
        """
        sio = sio or socketio.AsyncClient()

        sio.event(self.connect)
        sio.event(self.disconnect)
        sio.on("OnGroupMsgs", self._group_msg_handler)
        sio.on("OnFriendMsgs", self._friend_msg_handler)
        sio.on("OnEvents", self._event_handler)

        try:
            delay = 1
            while True:
                try:
                    logger.info(f"Connecting to the server[{self.config.address}]...")
                    await sio.connect(self.config.address, transports=["websocket"])
                except (SioConnectionError, ValueError):
                    current_delay = delay + (2 * random.random() - 1) / 2
                    logger.error(
                        f"连接失败，请检查ip端口是否配置正确，检查机器人是否启动，确保能够连接上! {current_delay:.1f} 后开始重试连接"
                    )
                    await asyncio.sleep(current_delay)
                    delay *= 1.68
                else:
                    break

            if wait:
                await sio.wait()

        except BaseException as e:
            await sio.disconnect()
            self.pool.shutdown(False)
            if isinstance(e, KeyboardInterrupt):
                print("\b\b\b\bbye~")
            else:
                raise

        return sio

    async def run_no_wait(self, sio: socketio.AsyncClient = None):
        """不阻塞运行"""
        return await self.run(False, sio)
