import httpx

from botoy import EventMsg, FriendMsg, GroupMsg, jconfig
from botoy.log import logger

# 以内置插件方式实现简单的webhook，将原始数据上报至指定地址
# 因为webhook功能只能通过配置文件开启，所以直接新建Config, 读取配置文件即可
# TODO: 处理响应，并进行简单的操作

url = jconfig.webhook_post_url
timeout = jconfig.webhook_timeout


def friend(ctx: FriendMsg):
    try:
        httpx.post(url, json=ctx.message, timeout=timeout)
    except Exception as e:
        logger.warning("Webhook请求中的错误: %s" % e)


def group(ctx: GroupMsg):
    try:
        httpx.post(url, json=ctx.message, timeout=timeout)
    except Exception as e:
        logger.warning("Webhook请求中的错误: %s" % e)


def event(ctx: EventMsg):
    try:
        httpx.post(url, json=ctx.message, timeout=timeout)
    except Exception as e:
        logger.warning("Webhook请求中的错误: %s" % e)


async def async_friend(ctx: FriendMsg):
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            await client.post(url, json=ctx.message)
    except Exception as e:
        logger.warning("Webhook请求中的错误: %s" % e)


async def async_group(ctx: GroupMsg):
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            await client.post(url, json=ctx.message)
    except Exception as e:
        logger.warning("Webhook请求中的错误: %s" % e)


async def async_event(ctx: EventMsg):
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            await client.post(url, json=ctx.message)
    except Exception as e:
        logger.warning("Webhook请求中的错误: %s" % e)
