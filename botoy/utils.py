"""提供框架所需的通用函数"""
import base64
import re


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
