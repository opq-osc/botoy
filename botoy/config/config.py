import json
import threading
from typing import Any, Generic, List, Optional, TypeVar, Union

from .constants import (
    CONFIG_FILE_PATH,
    DEFAULT_BLOCKED_USERS,
    DEFAULT_FRIEND_BLACKLIST,
    DEFAULT_GROUP_BLACKLIST,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_WEBHOOK,
    DEFAULT_WEBHOOK_POST_URL,
    DEFAULT_WEBHOOK_TIMEOUT,
)
from .util import dict2tree, lookup

V = TypeVar("V")
T = TypeVar("T")

lock = threading.RLock()

botoy_config = {
    "host": DEFAULT_HOST,
    "port": DEFAULT_PORT,
    "group_blacklist": DEFAULT_GROUP_BLACKLIST,
    "friend_blacklist": DEFAULT_FRIEND_BLACKLIST,
    "blocked_users": DEFAULT_BLOCKED_USERS,
    "webhook": DEFAULT_WEBHOOK,
    "webhook_post_url": DEFAULT_WEBHOOK_POST_URL,
    "webhook_timeout": DEFAULT_WEBHOOK_TIMEOUT,
}
botoy_config_tree = dict2tree(botoy_config)


def read_botoy_config():
    global botoy_config, botoy_config_tree

    with lock:
        try:
            botoy_config.update(json.loads(CONFIG_FILE_PATH.read_text()))
        except FileNotFoundError:
            pass

        botoy_config_tree = dict2tree(botoy_config)


read_botoy_config()


def write_botoy_config():
    with lock:
        CONFIG_FILE_PATH.write_text(
            json.dumps(botoy_config, ensure_ascii=False, indent=2), "utf8"
        )


def update_botoy_config(key, value):
    global botoy_config, botoy_config_tree

    with lock:
        if isinstance(value, type(...)):
            try:
                del botoy_config[key]
            except Exception:
                pass
        else:
            botoy_config[key] = value

        botoy_config_tree = dict2tree(botoy_config)

        write_botoy_config()


class Configuration(Generic[V]):
    def __init__(self, config_tree, section):
        self._section = section or ""
        self._config_tree = config_tree

    def get(self, key: str, default=None) -> Union[V, Any]:
        """从该配置获取配置值
        :param key: 需要获取的配置名，支持点连接(_._)命名
        :param default: 当配置值不存在时返回的值，默认为`None`
        """
        try:
            return lookup(self._config_tree, key)
        except KeyError:
            return default

    def has(self, key: str) -> bool:
        """检查配置名是否存在
        :param key: 配置名，支持点连接(_._)命名
        """
        try:
            lookup(self._config_tree, key)
            return True
        except KeyError:
            return False

    def update(self, key: str, value=None):
        """更新该配置中的配置
        :param key: 配置名，支持点连接(_._)命名
        :param value: 配置值，特殊情况，当value类型为 `ellipsis` 也就是 `...`时表示删除该项配置
        """
        full_key = self._section and self._section + "." + key or key
        update_botoy_config(full_key, value)

    def __getitem__(self, _: T) -> "Configuration[T]":
        return self  # type: ignore

    def __repr__(self) -> str:
        return "Configuration(tree=%s)" % self._config_tree.__repr__()


class Configurations:
    _instance: Optional["Configurations"] = None

    # 框架专属配置
    host: str
    port: int
    group_blacklist: List[int]
    friend_blacklist: List[int]
    blocked_users: List[int]
    webhook: bool
    webhook_post_url: str
    webhook_timeout: int

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_configuration(self, section: Optional[str] = None) -> Configuration:
        """获取一个该sectoin的配置对象"""
        try:
            config_tree = lookup(botoy_config_tree, section)
        except KeyError:
            config_tree = {}
        return Configuration(config_tree, section)

    # 兼容旧版API
    def get(self, key: str, default=None):
        """配置文件作为字典，此方法等于字典的get方法"""
        return botoy_config.get(key, default)

    def __getitem__(self, key: str):
        return botoy_config.get(key)

    def __getattr__(self, key: str):
        return botoy_config.get(key)

    ############

    def __repr__(self):
        return "Configurations(\n  data=%s\n  tree=%s\n)" % (
            botoy_config,
            botoy_config_tree,
        )


jconfig = Configurations()
