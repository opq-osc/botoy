import os
from pathlib import Path
from typing import List

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
DEFAULT_BLOCKED_USERS: List[int] = []
DEFAULT_WEBHOOK = False
DEFAULT_WEBHOOK_POST_URL = "http://127.0.0.1:5000"
DEFAULT_WEBHOOK_TIMEOUT = 20

CONFIG_FILE_PATH = Path.cwd() / "botoy.json"
