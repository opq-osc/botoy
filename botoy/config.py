import json
from typing import List

from .exceptions import InvalidConfigError
from .utils import check_schema

# | host             | ip或域名                           | 127.0.0.1      |
# | port             | 端口，也可以不需要                 | 8888           |
# | group_blacklist  | 群消息黑名单                       | []             |
# | friend_blacklist | 好友消息黑名单                     | []             |
# | blocked_users    | 用户黑名单，即包括群消息和好友消息 | []             |
# | webhook          | 是否开启webhook功能                | false          |
# | webhook_post_url | webhook上报地址                    | 127.0.0.1:5000 |
# | webhook_timeout  | webhook等待响应的延时              | 20             |

DEFAULT_HOST = "http://127.0.0.1"
DEFAULT_PORT = 8888
DEFAULT_GROUP_BLACKLIST: List[int] = []
DEFAULT_FRIEND_BLACKLIST: List[int] = []
DEFAULT_BLOCK_UESRS: List[int] = []
DEFAULT_WEBHOOK = False
DEFAULT_WEBHOOK_POST_URL = "http://127.0.0.1:5000"
DEFAULT_WEBHOOK_TIMEOUT = 20

# parametor > config file > default
class Config:
    # read botoy.json configuration
    jconfig = {}
    try:
        with open("botoy.json", encoding="utf-8") as f:
            jconfig = json.load(f)
    except FileNotFoundError:
        pass
    except Exception as e:
        raise InvalidConfigError("配置文件不规范") from e

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
        jconfig = self.jconfig
        self.host: str = check_schema(
            host or jconfig.get("host") or DEFAULT_HOST
        ).strip("/")
        self.port: int = int(port or jconfig.get("port") or DEFAULT_PORT)
        self.group_blacklist: List[int] = list(
            group_blacklist or jconfig.get("group_blacklist") or DEFAULT_GROUP_BLACKLIST
        )
        self.friend_blacklist: List[int] = list(
            friend_blacklist
            or jconfig.get("friend_blacklist")
            or DEFAULT_FRIEND_BLACKLIST
        )
        self.blocked_users: List[int] = list(
            blocked_users or jconfig.get("blocked_users") or DEFAULT_BLOCK_UESRS
        )
        self.webhook: bool = webhook or jconfig.get("webhook") or DEFAULT_WEBHOOK
        self.webhook_post_url: str = (
            webhook_post_url
            or jconfig.get("webhook_post_url")
            or DEFAULT_WEBHOOK_POST_URL
        )
        self.webhook_timeout: int = int(
            webhook_timeout or jconfig.get("webhook_timeout") or DEFAULT_WEBHOOK_TIMEOUT
        )

    @property
    def address(self):
        if self.port in (0, 80):
            return self.host
        return f"{self.host}:{self.port}"

    def get_jconfig(self, config_name):
        """获取botoy.json内的配置, 如果不存在就返回None
        :config_name: 配置的名称
        """
        return self.jconfig.get(config_name)

    def __getattr__(self, attr):
        return self.jconfig.get(attr)


jconfig = Config()
