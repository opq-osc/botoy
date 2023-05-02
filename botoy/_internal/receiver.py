import inspect
import os
from pathlib import Path
from typing import Callable, Coroutine, List, Tuple, Union
from uuid import uuid4


class ReceiverMarker:
    def __call__(
        self,
        receiver,
        name="",
        author="",
        usage="",
        *,
        _directly_attached=False,
        _back=1,
    ):
        """标记接收函数
        该信息仅用于开发者调试
        :param receiver: 接收函数
        :param name: 插件名称，默认为__name__
        :param author: 插件作者，默认为空
        :param usage: 插件用法，默认为__doc__
        """
        receiver.__dict__["is_receiver"] = True
        meta = ""
        if file := inspect.getsourcefile(receiver):
            meta += str(Path(file).relative_to(os.getcwd()))
        try:
            lines = inspect.getsourcelines(receiver)
            if meta:
                meta += " line {}".format(lines[1])
        except:
            pass

        receiver.__dict__["_info"] = ReceiverInfo(
            **{
                "author": author or "",
                "usage": usage or receiver.__doc__ or "",
                "name": name or receiver.__name__ or "",
                "meta": meta or "",
            }
        )

        # 插件通过加入额外信息标记接收函数, 其前提该函数能在import后的module中`被检索`到
        # 被attach调用时，函数会被直接添加，所以无需进行该操作
        if not _directly_attached:
            frame = inspect.currentframe()
            for _ in range(_back):
                frame = frame.f_back  # type: ignore
            _globals = frame.f_globals  # type: ignore
            if receiver not in _globals.values():
                u = "receiver" + str(uuid4())
                _globals[u] = receiver
        return self

    def __add__(self, receiver: Union[Callable, Tuple, List]):
        if receiver == self:
            pass
        elif callable(receiver):
            self(receiver, _back=2)
        elif isinstance(receiver, (List, Tuple)):
            items = list(receiver)
            items.extend(["", "", ""])
            self(items[0], *items[1:3], _back=2)
        else:
            # TODO ???
            pass
        return self


mark_recv = ReceiverMarker()


def is_recv(receiver):
    try:
        return receiver.__dict__.get("is_receiver", False)
    except Exception:
        return False


class ReceiverInfo:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.author = kwargs.get("author", "")
        self.usage = kwargs.get("usage", "")
        self.meta = kwargs.get("meta", "")


class Receiver:
    def __init__(self, callback: Callable[[], Coroutine], info=None):
        self.callback = callback
        self.info = info or ReceiverInfo()

    async def __call__(self):
        await self.callback()
