"""
插件仅作为模块导入，提供receive_group_msg, receive_friend_msg, receive_events 函数

插件位于plugins目录:
    单文件: bot_pluginA.py  (插件标记为 pluginA)
    包：bot_pluginB (插件标记为pluginB)
        包支持子目录提供插件同样支持包和文件夹形式, 最多二级子目录
        bot_pluginB_sub1.py (插件标记为pluginB.sub1)
        bot_pluginB_sub2 (插件标记为pluginB.sub2)
"""
import importlib
import os
import re
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple

import colorama
from prettytable import PrettyTable

from .typing import T_EventReceiver, T_FriendMsgReceiver, T_GroupMsgReceiver


def resolve_plugin_name(name: str) -> str:
    # plugins.bot_a
    # plugins.bot_a.bot_b
    names = re.findall(r"bot_(\w+)", name)
    if names:
        return ".".join(names)
    return name


class Plugin:
    def __init__(self, import_path: str):
        self.import_path = import_path
        self.module: Optional[ModuleType] = None
        self._enabled = True
        self._name = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False
        if self.module:
            when_disable = self.module.__dict__.get("when_disable")
            if when_disable:
                when_disable()

    @property
    def when_connected(self) -> Optional[Callable[[List[int], str, int], Any]]:
        return self.module.__dict__.get("when_connected")

    @property
    def when_disconnected(self) -> Optional[Callable[[List[int], str, int], Any]]:
        return self.module.__dict__.get("when_disconnected")

    @property
    def loaded(self) -> bool:
        return self.module is not None

    def load(self) -> "Plugin":
        self.module = importlib.import_module(self.import_path)
        return self

    def reload(self) -> "Plugin":
        if self.module is not None:
            self.module = importlib.reload(self.module)
        return self

    @property
    def help(self) -> str:
        if self.module is not None:
            return self.module.__doc__ or ""
        return ""

    @property
    def name(self) -> str:
        if self.module is not None:
            return resolve_plugin_name(self.module.__name__)
        return ""

    @property
    def receive_group_msg(self) -> Optional[T_GroupMsgReceiver]:
        return self.module.__dict__.get("receive_group_msg")

    @property
    def receive_friend_msg(self) -> Optional[T_FriendMsgReceiver]:
        return self.module.__dict__.get("receive_friend_msg")

    @property
    def receive_events(self) -> Optional[T_EventReceiver]:
        return self.module.__dict__.get("receive_events")


CACHE_PATH = Path("REMOVED_PLUGINS")


def read_removed_plugins() -> List[str]:
    with open(CACHE_PATH) as f:
        return [line.strip("\n").strip() for line in f.readlines() if line.strip()]


def write_removed_plugins(plugins: List[str]):
    with open(CACHE_PATH, "w") as f:
        print(*plugins, file=f, sep="\n")


class PluginManager:
    def __init__(self) -> None:
        self.plugins_dir: Path = Path("plugins")
        # 插件的导入路径作为键, 也是所说的插件id
        self.plugins: Dict[str, Plugin] = dict()

    def cache(self):
        plugins = []
        for id, plugin in self.plugins.items():
            if not plugin.enabled:
                plugins.append(id)
        write_removed_plugins(plugins)

    def load_plugins(self) -> None:
        """加载插件"""
        CACHE_PATH.touch()
        # 整理所有插件的导入路径
        # 如果是包形式，则还需要多读取一级目录
        def clean_path(name) -> Optional[str]:
            matched = re.match(r"(bot_\w+)", name)
            if matched:
                return matched.group(1)
            return None

        # 能直接被import的路徑
        paths = []

        for name in os.listdir(self.plugins_dir):
            path = clean_path(name)
            if not path:
                continue
            paths.append(f"plugins.{path}")

            name_obj = self.plugins_dir / name
            if name_obj.is_dir():
                for subname in os.listdir(name_obj):
                    path = clean_path(subname)
                    if path:
                        paths.append(f"plugins.{name}.{path}")

        # 初始化插件实例
        removed_plugins = read_removed_plugins()
        for path in paths:
            id_ = resolve_plugin_name(path)
            plugin = Plugin(path)
            if id_ in removed_plugins:
                plugin.disable()
            self.plugins[id_] = plugin
        # 加载插件
        for plugin in self.plugins.values():
            if plugin.enabled:
                plugin.load()

    def reload_plugin(self, id_or_name: str) -> bool:
        """重载指定插件, 插件不存在或未启用则返回``False``
        :param id_or_name: 插件id或插件名
        """
        for id, plugin in self.plugins.items():
            if plugin.enabled and id_or_name in (id, plugin.name):
                plugin.reload()
                return True
        return False

    def disable_plugin(self, id_or_name: str) -> bool:
        """停用指定插件, 插件不存在或未启用则返回``False``
        :param id_or_name: 插件id或插件名
        """
        for id, plugin in self.plugins.items():
            if plugin.enabled and id_or_name in (id, plugin.name):
                plugin.disable()
                self.cache()
                return True
        return False

    def enable_plugin(self, id_or_name: str) -> bool:
        """启用指定插件, 插件不存在或未停用则返回``False``
        :param id_or_name: 插件id或插件名
        """
        for id, plugin in self.plugins.items():
            if not plugin.enabled and id_or_name in (id, plugin.name):
                plugin.enable()
                self.cache()
                # 位于缓存移除插件列表的插件启动时并不会加载
                # 所以这里中途启用的话需要判断并加载一次
                if not plugin.loaded:
                    plugin.load()
                return True
        return False

    def reload_plugins(self, include_new: bool = True):
        """重新加载插件
        :param include_new: 为``True``的话将会同时加载新创建的插件
        """
        for plugin in self.plugins.values():
            if plugin.enabled:
                plugin.reload()
        if include_new:
            self.load_plugins()

    @property
    def all_plugins(self) -> List[Tuple[str, str]]:
        """返回当前所有插件信息
        返回值是一个元组列表，元组有两项，第一项为插件id，第二项为插件名
        """
        plugins = []
        for id, plugin in self.plugins.items():
            plugins.append((id, plugin.name))
        return plugins

    @property
    def enabled_plugins(self) -> List[Tuple[str, str]]:
        """返回当前已启用插件信息
        返回值是一个元组列表，元组有两项，第一项为插件id，第二项为插件名
        """
        plugins = []
        for id, plugin in self.plugins.items():
            if plugin.enabled:
                plugins.append((id, plugin.name))
        return plugins

    @property
    def disabled_plugins(self) -> List[Tuple[str, str]]:
        """返回当前已停用插件信息
        返回值是一个元组列表，元组有两项，第一项为插件id，第二项为插件名
        """
        plugins = []
        for id, plugin in self.plugins.items():
            if not plugin.enabled:
                plugins.append((id, plugin.name))
        return plugins

    @property
    def friend_msg_receivers(self) -> List[T_FriendMsgReceiver]:
        """插件所提供的所有好友消息接收函数"""
        receivers = []
        for plugin in self.plugins.values():
            if plugin.enabled and plugin.receive_friend_msg is not None:
                receivers.append(plugin.receive_friend_msg)
        return receivers

    @property
    def group_msg_receivers(self) -> List[T_GroupMsgReceiver]:
        """插件所提供的所有群消息接收函数"""
        receivers = []
        for plugin in self.plugins.values():
            if plugin.enabled and plugin.receive_group_msg is not None:
                receivers.append(plugin.receive_group_msg)
        return receivers

    @property
    def event_receivers(self) -> List[T_EventReceiver]:
        """插件所提供的所有事件接收函数"""
        receivers = []
        for plugin in self.plugins.values():
            if plugin.enabled and plugin.receive_events is not None:
                receivers.append(plugin.receive_events)
        return receivers

    @property
    def when_connected_funcs(self) -> List[Callable[[List[int], str, int], Any]]:
        funcs = []
        for plugin in self.plugins.values():
            if plugin.enabled and plugin.when_connected:
                funcs.append(plugin.when_connected)
        return funcs

    @property
    def when_disconnected_funcs(self) -> List[Callable[[List[int], str, int], Any]]:
        funcs = []
        for plugin in self.plugins.values():
            if plugin.enabled and plugin.when_disconnected:
                funcs.append(plugin.when_disconnected)
        return funcs

    @property
    def info(self) -> str:
        """插件信息"""
        enabled_plugin_table = PrettyTable(
            ["PLUGIN NAME", "GROUP MESSAGE", "FRIEND MESSAGE", "EVENT", "HELP"]
        )
        disabled_plugin_table = PrettyTable(["REMOVED PLUGINS"])

        color = colorama.Fore.BLUE
        for id, plugin in self.plugins.items():
            color = (
                colorama.Fore.GREEN
                if color == colorama.Fore.BLUE
                else colorama.Fore.BLUE
            )

            def c(msg) -> str:
                return f"{color}{msg}{colorama.Style.RESET_ALL}"

            if id == plugin.name:
                name = id
            else:
                name = f"{id}({plugin.name})"

            if plugin.enabled:
                enabled_plugin_table.add_row(
                    [
                        c(name),
                        c("√" if plugin.receive_group_msg else ""),
                        c("√" if plugin.receive_friend_msg else ""),
                        c("√" if plugin.receive_events else ""),
                        c(plugin.help or ""),
                    ]
                )
            else:
                disabled_plugin_table.add_row([c(name)])

        return str(enabled_plugin_table) + "\n" + str(disabled_plugin_table)

    @property
    def help(self) -> str:
        """所有的插件帮助信息"""
        return "\n".join(
            ["※ " + plugin.help for plugin in self.plugins.values() if plugin.help]
        )

    def get_plugin_help(self, id_or_name: str) -> str:
        """获取单个插件的帮助信息"""
        for id, plugin in self.plugins.items():
            if id_or_name in (id, plugin.name):
                return plugin.help
        return ""
