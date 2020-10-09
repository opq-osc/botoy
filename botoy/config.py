from typing import List

from botoy import json
from botoy.exceptions import InvalidConfigError
from botoy.util import check_schema

# | host             | ip或域名                           | 127.0.0.1 |
# | port             | 端口，也可以不需要                 | 8888      |
# | group_blacklist  | 群消息黑名单                       | []        |
# | friend_blacklist | 好友消息黑名单                     | []        |
# | blocked_users    | 用户黑名单，即包括群消息和好友消息 | []        |
# | webhook          | 是否开启webhook功能                | false     |
# | webhook_post_url | webhook上报地址                    | None      |
# | webhook_timeout  | webhook等待响应的延时              | 20        |


# 写得很乱，总之就是优先指定的参数值，然后文件中的配置值，最后默认值
class Config:
    def __init__(
        self,
        host: str = None,
        port: int = None,
        group_blacklist: List[int] = None,
        friend_blacklist: List[int] = None,
        blocked_users: List[int] = None,
        webhook: bool = None,
        webhook_post_url: str = None,
        webhook_timeout: int = None,
    ):
        self.host = host
        self.port = port
        self.group_blacklist = group_blacklist
        self.friend_blacklist = friend_blacklist
        self.blocked_users = blocked_users
        self.webhook = webhook
        self.webhook_post_url = webhook_post_url
        self.webhook_timeout = webhook_timeout
        self.load_file()

    def load_file(self):
        _c = {}
        try:
            with open('botoy.json', encoding='utf-8') as f:
                _c = json.load(f)
        except FileNotFoundError:
            pass
        except json.JSONDecodeError as e:
            raise InvalidConfigError('配置文件不规范') from e

        # host
        if self.host is None:
            host = _c.get('host')
            if host is None:
                self.host = 'http://127.0.0.1'
            else:
                self.host = check_schema(host)

        # port
        if self.port is None:
            port = _c.get('port')
            if port is None:  # 没有配置用默认值
                self.port = 8888
            elif port == 0:  # 配置为0, 则不用端口, 比如单独一个域名
                self.port = 0
            else:
                self.port = int(port)

        # group_blacklist
        if self.group_blacklist is None:
            self.group_blacklist = _c.get('group_blacklist') or list()

        # friend_blacklist
        if self.friend_blacklist is None:
            self.friend_blacklist = _c.get('friend_blacklist') or list()

        # blocked_users
        if self.blocked_users is None:
            self.blocked_users = _c.get('blocked_users') or list()

        # webhook
        if self.webhook is None:
            self.webhook = bool(_c.get('webhook'))

        if self.webhook:
            # webhook_post_url
            if self.webhook_post_url is None:
                webhook_post_url = _c.get('webhook_post_url')
                self.webhook_post_url = check_schema(webhook_post_url)
            else:
                self.webhook_post_url = check_schema(self.webhook_post_url)
            # webhook_timeout
            webhook_timeout = _c.get('webhook_timeout')
            if webhook_timeout is None:
                self.webhook_timeout = 20

    @property
    def address(self) -> str:
        # address 由host和port拼接
        if self.port == 0:
            return self.host
        return f'{self.host}:{self.port}'
