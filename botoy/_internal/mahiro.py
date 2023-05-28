import asyncio
from typing import Optional
from urllib.parse import urlparse

import httpx
import uvicorn
from fastapi import FastAPI, Request

from .client import Botoy
from .config import jconfig
from .log import logger

# botoy.json 新增项
# mahiro_listen_url: botoy服务端监听地址，如 0.0.0.0:8099
# mahiro_server_url: mahiro服务地址，如 http://0.0.0.0:8098
# 以上默认值与mahiro中默认值一致
#


class Mahiro(Botoy):
    def __init__(self):
        super().__init__()
        self.app = FastAPI()
        self._token = ""
        mahiro = jconfig.get_configuration("mahiro")
        address = mahiro.get("listen_url", "http://0.0.0.0:8099")
        if not address.startswith("http"):
            self.default_address = f"http://{address}"
        server = mahiro.get("server_url", "http://localhost:8098")
        if not server.startswith("http"):
            server = f"http://{server}"
        self.REGISTER_PLUGIN_URL = f"{server}/api/v1/panel/plugin/register"
        self.GET_TOKEN_URL = f"{server}/api/v1/panel/auth/gettoken"
        self.__setup_routes()

    def set_token(self, token: str):
        self._token = token

    @property
    def headers(self):
        return {"x-mahiro-token": self._token}

    async def __message_handler(self, req: Request):
        await self.__ensure_token()
        data = await req.json()
        self._start_task(
            self._packet_handler,
            data["raw"],
            _available_names=data.get("configs", {}).get("availablePlugins", []),
        )
        return {"code": 200}

    async def __exchange_authentication(self, req: Request):
        data = await req.json()
        self.set_token(data["token"])
        for receiver in self.receivers:
            name = "BOTOY " + receiver.info.name
            httpx.post(
                self.REGISTER_PLUGIN_URL,
                headers=self.headers,
                json={"name": name},
                timeout=20,
            )
            logger.info("Registered mahiro plugin: " + name)

    async def __request_token(self):
        async with httpx.AsyncClient() as client:
            await client.post(self.GET_TOKEN_URL, timeout=20)

    async def __ensure_token(self):
        times = 0
        while self._token == "" and times < 120:  # 重试这么多次不行就打120吧
            times += 1
            await self.__request_token()
            # 留时间给server端把token传过来
            await asyncio.sleep(2)  # 先留2秒应该够了
            if self._token:
                break
            # 不够再加
            await asyncio.sleep(2)

    def __setup_routes(self):
        self.app.post("/recive/group")(self.__message_handler)
        self.app.post("/recive/friend")(self.__message_handler)
        self.app.get("/recive/health")(lambda: {"code": 200, "version": "1.5.0"})
        self.app.post("/recive/auth")(self.__exchange_authentication)

    def listen(
        self,
        # 把这个参数删掉？完全用jconfig配置!
        address: Optional[str] = "",
        reload: bool = False,
    ):
        # TODO: 文档中要说明配置项
        address = address or self.default_address
        p = urlparse(address)
        host, port = p.hostname, p.port
        if host and port:
            uvicorn.run(app=self.app, port=port, host=host, reload=reload)
        else:
            logger.error(f"不支持的地址：{address}")
