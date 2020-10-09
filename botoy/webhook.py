import httpx

from botoy import EventMsg, FriendMsg, GroupMsg
from botoy.config import Config
from botoy.log import logger

# 以内置插件方式实现简单的webhook，将原始数据上报至指定地址
# 因为webhook功能只能通过配置文件开启，所以直接新建Config, 读取配置文件即可
# TODO: resolve response

_config = Config()
_c = httpx.Client(base_url=_config.address, timeout=_config.webhook_timeout)


def receive_friend_msg(ctx: FriendMsg):
    try:
        _c.post(httpx.URL(), json=ctx.message)
    except Exception as e:
        logger.warning('Webhook请求中的错误: %s' % e)


def receive_group_msg(ctx: GroupMsg):
    try:
        _c.post(httpx.URL(), json=ctx.message)
    except Exception as e:
        logger.warning('Webhook请求中的错误: %s' % e)


def receive_events(ctx: EventMsg):
    try:
        _c.post(httpx.URL(), json=ctx.message)
    except Exception as e:
        logger.warning('Webhook请求中的错误: %s' % e)
