import importlib
from pathlib import Path
from typing import Callable

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
        return getattr(self.L, attr)

    def __init__(self, *args, **kwargs) -> None:
        self.L = BaseLuaRuntime(*args, **kwargs)  # uninheritable
        self.to_lua_function = lambda f: self.eval(
            "function (f) return function(...) return f(...) end end"
        )(f)
        self.g = self.globals()
        g = self.g
        g.package.path = package_path + g.package.path
        g['import'] = self.to_lua_function(importlib.import_module)
        g.opq = self.table_from({})
        self.execute("opq.none = python.none")
        g.python = None
        self.require('_init_packages')
