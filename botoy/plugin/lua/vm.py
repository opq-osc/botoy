import importlib

from ._lupa import LuaRuntime


def init_vm(L: LuaRuntime):
    g = L.globals()
    g["python"] = None
    g["import"] = importlib.import_module
    g["package"]["path"] = (
        "./plugins/?.lua;./plugins/?/init.lua;" + g["package"]["path"]
    )
    return L
