import importlib
from pathlib import Path
from typing import Callable, Dict, Iterable

try:
    from lupa import LuaRuntime as BaseLuaRuntime  # type: ignore
except ImportError:

    class BaseLuaRuntime:
        def __init__(self, *_, **__):
            __import__("lupa")


lib_path = Path(__file__).absolute().parent / 'lua'

package_path = f"./plugins/?.lua;./plugins/?/init.lua;{lib_path / '?.lua'};{lib_path / '?' / 'init.lua'};"


class LuaRuntime:
    globals: Callable
    table_from: Callable
    eval: Callable
    execute: Callable
    require: Callable

    def __getattr__(self, attr):
        value = self.__dict__[attr] = getattr(self.L, attr)
        return value

    def __init__(self, *args, **kwargs) -> None:
        self.L = BaseLuaRuntime(*args, **kwargs)  # uninheritable
        self.to_lua_function = lambda f: self.eval(
            "function (f) return function(...) return f(...) end end"
        )(f)
        self.g = self.globals()
        g = self.g
        g.package.path = package_path + g.package.path
        g['import'] = self.to_lua_function(importlib.import_module)
        g._to_lua_table = self.to_lua_table
        g.opq = self.table_from({})
        self.execute("opq.none = python.none")
        g.python = None
        self.require('_init_packages')

    def to_lua_table(self, data):
        # only convert dict and list
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self.to_lua_table(value)
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                data[idx] = self.to_lua_table(item)
        else:
            return data
        return self.table_from(data)

    @property
    def receive_group_msg(self):
        receiver = self.g.receive_group_msg
        if receiver:
            return lambda ctx: receiver(
                self.to_lua_table(dict(bot=ctx.CurrentQQ, data=ctx.data, ctx=ctx))
            )

    @property
    def receive_friend_msg(self):
        receiver = self.g.receive_friend_msg
        if receiver:
            return lambda ctx: receiver(
                self.to_lua_table(dict(bot=ctx.CurrentQQ, data=ctx.data, ctx=ctx))
            )

    @property
    def receive_events(self):
        receiver = self.g.receive_events
        if receiver:
            return lambda ctx: receiver(
                self.to_lua_table(dict(bot=ctx.CurrentQQ, data=ctx.data, ctx=ctx))
            )
