import json
import os
from typing import Any, List

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

DEFAULT_HOST = os.getenv("BOTOY_HOST") or "http://127.0.0.1"
DEFAULT_PORT = int(os.getenv("BOTOY_PORT") or 8888)
DEFAULT_GROUP_BLACKLIST: List[int] = []
DEFAULT_FRIEND_BLACKLIST: List[int] = []
DEFAULT_BLOCK_UESRS: List[int] = []
DEFAULT_WEBHOOK = False
DEFAULT_WEBHOOK_POST_URL = "http://127.0.0.1:5000"
DEFAULT_WEBHOOK_TIMEOUT = 20

CONFIG_FILE_NAME = "botoy.json"

try:
    with open(CONFIG_FILE_NAME, encoding="utf-8") as f:
        botoy_json = json.load(f)
except FileNotFoundError:
    botoy_json = {}
except Exception as e:
    raise InvalidConfigError("配置文件不规范") from e

# parametor > config file > default
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
        config: dict = None,
    ):
        self.config = config or botoy_json

        self.host: str = check_schema(
            host or self.config.get("host") or DEFAULT_HOST
        ).strip("/")
        self.port: int = int(port or self.config.get("port") or DEFAULT_PORT)
        self.group_blacklist: List[int] = list(
            group_blacklist
            or self.config.get("group_blacklist")
            or DEFAULT_GROUP_BLACKLIST
        )
        self.friend_blacklist: List[int] = list(
            friend_blacklist
            or self.config.get("friend_blacklist")
            or DEFAULT_FRIEND_BLACKLIST
        )
        self.blocked_users: List[int] = list(
            blocked_users or self.config.get("blocked_users") or DEFAULT_BLOCK_UESRS
        )
        self.webhook: bool = webhook or self.config.get("webhook") or DEFAULT_WEBHOOK
        self.webhook_post_url: str = (
            webhook_post_url
            or self.config.get("webhook_post_url")
            or DEFAULT_WEBHOOK_POST_URL
        )
        self.webhook_timeout: int = int(
            webhook_timeout
            or self.config.get("webhook_timeout")
            or DEFAULT_WEBHOOK_TIMEOUT
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
        return self.config.get(config_name)

    def __getattr__(self, attr) -> Any:
        return self.config.get(attr)

    def get_section(self, section_name: str):
        """获取该字段所对应的数据
        - 如果数据是字典类型，则返回一个新的Config对象，新的Config的方法对该数据进行处理
        - 如果是其他类型数据，将直接返回
        - 不存在则返回None

        例如botoy.json为

        ```json
        {
            "A": {
                "B": "value of B"
                "C": ["item1", "item2"]
            }
        }
        ```
        那么
        ```python
        config = Config()

        assert config.A == {"B":"value of B", "C": ["item1", "item2"]}
        assert config.A["B"] == "value of B"

        section_a = config.get_section("A")
        assert section_a.B == "value of B"

        section_a_b = section_a.get_("B")
        assert section_a_b == "value of B"

        section_a_c = section_a.get_("C")
        assert section_a_c == ["item1", "item2"]
        ```

        """
        section = self.config.get(section_name)
        if isinstance(section, dict):
            return Config(config=section)
        return section


jconfig = Config()
