"""提供框架所需的通用函数"""
import asyncio
import base64
import re
import warnings
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, Union


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

        def __str__(self):
            return str(contextvar.get())

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


try:
    import cv2
    import numpy as np

    def _get_image_size(target: Union[bytes, BytesIO, str, Path]) -> Tuple[int, int]:  # type: ignore
        """获取图像尺寸
        :param target: 目标图像。接收图像路径或图像二进制数据
        :return: (长, 宽)
        """
        if isinstance(target, (bytes, BytesIO)):
            if isinstance(target, BytesIO):
                target.seek(0)
                target = target.read()
            arr = np.frombuffer(target, np.uint8)  # type: ignore
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)  # type: ignore
        elif isinstance(target, (str, Path)):
            img = cv2.imread(target.absolute() if isinstance(target, Path) else target)  # type: ignore
        else:
            raise TypeError("参数类型有误")
        h, w = img.shape[:2]
        return h, w

except ImportError:
    try:
        from PIL import Image

        def _get_image_size(target: Union[bytes, BytesIO, str, Path]) -> Tuple[int, int]:  # type: ignore
            """获取图像尺寸
            :param target: 目标图像。接收图像路径或图像二进制数据
            :return: (长, 宽)
            """
            if isinstance(target, str):
                target = Path(target)
            elif isinstance(target, bytes):
                target = BytesIO(target)
            img = Image.open(target)
            w, h = img.size
            return h, w

    except ImportError:

        def _get_image_size(_):  # type: ignore
            warnings.warn("为了让发送的图片有较好的预览效果，请安装 opencv-python 或者 pillow")
            return None


def get_image_size(
    target: Union[bytes, BytesIO, str, Path]
) -> Optional[Tuple[int, int]]:
    """获取图像尺寸
    :param target: 目标图像。接收图像路径或图像二进制数据
    :return: (长, 宽)
    """
    return _get_image_size(target)
