try:
    from lupa import LuaRuntime as LuaRuntime  # type: ignore
except ImportError:

    class LuaRuntime:
        def __init__(self, *_, **__):
            __import__("lupa")

        def globals(self):
            return {}

        def execute(self, *_):
            pass
