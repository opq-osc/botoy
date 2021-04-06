import copy
import importlib
import os
import pathlib
import re
from types import ModuleType
from typing import Dict, List

from prettytable import PrettyTable

from botoy import json


class Plugin:
    def __init__(self, module: ModuleType):
        self.module = module

        # plugin help
        with open(self.module.__file__, encoding='utf8') as f:
            line_one = f.readline().strip()
        if line_one.startswith('#'):
            self.help = line_one[1:].strip()
        else:
            self.help = ""

    def reload(self):
        self.module = importlib.reload(self.module)

    @property
    def name(self):
        return self.module.__name__.split('.')[-1][4:]

    @property
    def receive_group_msg(self):
        return self.module.__dict__.get('receive_group_msg')

    @property
    def receive_friend_msg(self):
        return self.module.__dict__.get('receive_friend_msg')

    @property
    def receive_events(self):
        return self.module.__dict__.get('receive_events')


def read_json_file(path) -> dict:
    with open(path, encoding='utf8') as f:
        return json.load(f)


def write_json_file(path, data) -> None:
    with open(path, 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False)


REMOVED_PLUGINS_FILE = pathlib.Path('REMOVED_PLUGINS')
REMOVED_PLUGINS_TEMPLATE = {'tips': '用于存储已停用插件信息,请不要修改这个文件', 'plugins': []}


class PluginManager:
    """通用插件管理类"""

    def __init__(self, plugin_dir: str = 'plugins'):
        self.plugin_dir = plugin_dir  # 插件文件夹
        self._plugins: Dict[str, Plugin] = dict()  # 已启用的插件
        self._removed_plugins: Dict[str, Plugin] = dict()  # 已停用的插件

        # 停用的插件名列表
        self._removed_plugin_names = []

    def _load_removed_plugin_names(self):
        """读取已移除插件名文件，初始化_removed_plugin_names，后面刷新插件时不再加载"""
        if REMOVED_PLUGINS_FILE.exists():
            self._removed_plugin_names = read_json_file(REMOVED_PLUGINS_FILE)['plugins']
        else:
            write_json_file(REMOVED_PLUGINS_FILE, REMOVED_PLUGINS_TEMPLATE)
            self._removed_plugin_names = []

    def _update_removed_plugin_names(self):
        """更新已移除插件名文件"""
        removed_plugins_data = copy.deepcopy(REMOVED_PLUGINS_TEMPLATE)
        removed_plugins_data['plugins'] = list(set(self._removed_plugin_names))
        write_json_file(REMOVED_PLUGINS_FILE, removed_plugins_data)

    def load_plugins(self, plugin_dir: str = None) -> None:
        """加载插件，只会加载新插件, 在调用其他方法前必须调用该方法一次"""
        self._load_removed_plugin_names()

        if plugin_dir is None:
            plugin_dir = self.plugin_dir
        plugin_files = (
            i for i in os.listdir(plugin_dir) if re.search(r'^bot_\w+\.py$', i)
        )
        for plugin_file in plugin_files:
            module = importlib.import_module(
                '{}.{}'.format(plugin_dir.replace('/', '.'), plugin_file.split('.')[0])
            )
            plugin = Plugin(module)
            if plugin.name in self._removed_plugin_names:
                self._removed_plugins[plugin.name] = plugin
            else:
                self._plugins[plugin.name] = plugin

    def reload_plugins(self, plugin_dir: str = None) -> None:
        """加载新插件并刷新旧插件"""
        # reload old
        old_plugins = self._plugins.copy()
        for old_plugin in old_plugins.values():
            old_plugins[old_plugin.name].reload()
        # load new
        self.load_plugins(plugin_dir)
        # tidy
        self._plugins.update(old_plugins)

    def reload_plugin(self, plugin_name: str) -> None:
        """根据指定插件名刷新插件，不管是否存在，都不会报错"""
        if plugin_name in self._plugins:
            self._plugins[plugin_name].reload()

    def remove_plugin(self, plugin_name: str) -> None:
        """移除指定插件, 不会报错"""
        try:
            if plugin_name in self._plugins:
                self._removed_plugins[plugin_name] = self._plugins.pop(plugin_name)
                # 缓存到本地
                self._removed_plugin_names.append(plugin_name)
                self._update_removed_plugin_names()
        except KeyError:  # 可能由self._removed_plugins[plugin_name]引发
            pass

    def recover_plugin(self, plugin_name: str) -> None:
        """重新开启指定插件, 不会报错"""
        try:
            if plugin_name in self._removed_plugins:
                self._plugins[plugin_name] = self._removed_plugins.pop(plugin_name)
                if plugin_name in self._removed_plugin_names:
                    self._removed_plugin_names.remove(plugin_name)
                    self._update_removed_plugin_names()
        except KeyError:
            pass

    @property
    def plugins(self) -> List[str]:
        '''return a list of plugin name'''
        return list(self._plugins)

    @property
    def removed_plugins(self) -> List[str]:
        '''return a list of removed plugin name'''
        return list(self._removed_plugins)

    @property
    def friend_msg_receivers(self):
        '''funcs to handle (friend msg)context'''
        return [
            plugin.receive_friend_msg
            for plugin in self._plugins.values()
            if plugin.receive_friend_msg
        ]

    @property
    def group_msg_receivers(self):
        '''funcs to handle (group msg)context'''
        return [
            plugin.receive_group_msg
            for plugin in self._plugins.values()
            if plugin.receive_group_msg
        ]

    @property
    def event_receivers(self):
        '''funcs to handle (event msg)context'''
        return [
            plugin.receive_events
            for plugin in self._plugins.values()
            if plugin.receive_events
        ]

    @property
    def info_table(self) -> str:
        table = PrettyTable(['Receiver', 'Count', 'Info'])
        table.add_row(
            [
                'Friend Msg Receiver',
                len(self.friend_msg_receivers),
                '/'.join(
                    [
                        f'{p.name}'
                        for p in self._plugins.values()
                        if p.receive_friend_msg
                    ]
                ),
            ]
        )
        table.add_row(
            [
                'Group  Msg Receiver',
                len(self.group_msg_receivers),
                '/'.join(
                    [f'{p.name}' for p in self._plugins.values() if p.receive_group_msg]
                ),
            ]
        )
        table.add_row(
            [
                'Event      Receiver',
                len(self.event_receivers),
                '/'.join(
                    [f'{p.name}' for p in self._plugins.values() if p.receive_events]
                ),
            ]
        )
        table_removed = PrettyTable(['Removed Plugins'])
        table_removed.add_row(['/'.join(self.removed_plugins)])
        return str(table) + '\n' + str(table_removed)

    @property
    def help(self) -> str:
        """返回已启用插件的帮助信息"""
        return "\n".join(
            ['※ ' + plugin.help for plugin in self._plugins.values() if plugin.help]
        )

    def get_plugin_help(self, plugin_name: str) -> str:
        """返回指定插件的帮助信息，如果插件不存在，则返回空"""
        plugin = {**self._plugins, **self._removed_plugins}.get(plugin_name)
        if plugin is not None:
            return plugin.help
        return ""
