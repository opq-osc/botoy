"""提供框架所需的通用函数"""
import asyncio
import base64
import re


def to_address(host, port) -> str:
    if port in (0, 80):
        return host
    return f"{host}:{port}"


def check_schema(url: str) -> str:
    url = url.strip("/")
    if not re.findall(r"(http://|https://)", url):
        return "http://" + url
    return url


def file_to_base64(path):
    """获取文件base64编码"""
    with open(path, "rb") as f:
        content = f.read()
    return base64.b64encode(content).decode()


def bind_contextvar(contextvar):
    class ContextVarBind:
        __slots__ = ()

        def __getattr__(self, name):
            return getattr(contextvar.get(), name)

        def __setattr__(self, name, value):
            setattr(contextvar.get(), name, value)

        def __delattr__(self, name):
            delattr(contextvar.get(), name)

        def __getitem__(self, index):
            return contextvar.get()[index]

        def __setitem__(self, index, value):
            contextvar.get()[index] = value

        def __delitem__(self, index):
            del contextvar.get()[index]

    return ContextVarBind()


def sync_run(func):
    """同步执行异步函数，获取结果(该函数始终新建一个事件循环)
    例如::

        async def hello(name=None):
            if name:
                return f'Hello {name}'
            return 'Hello'


        print(sync_run(hello()))  # Hello
        print(sync_run(hello('World')))  # Hello World
    """
    loop = asyncio.new_event_loop()
    coro = asyncio.iscoroutine(func) and func or func()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
