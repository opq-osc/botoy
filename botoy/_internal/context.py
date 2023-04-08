import traceback
from typing import Any, AnyStr, List, Optional, Union
from contextvars import ContextVar

from pydantic import BaseModel

from . import models
from .utils import bind_contextvar


def c(obj, key, value):  # c => cache
    obj.__dict__[key] = value
    return value


class GroupMsg:
    def __init__(self, data: Union[str, dict]):
        if isinstance(data, str):
            model = models.GroupMsg.parse_raw(data)
        else:
            model = models.GroupMsg(**data)

        assert (
            model.CurrentPacket.EventData.MsgHead.C2cCmd
            == model.CurrentPacket.EventData.MsgHead.C2cCmd.integer_0
        ), "GroupMsg: C2cCmd == 0"

        self.__model = model

    @property
    def model(self) -> models.GroupMsg:
        return self.__model

    @property
    def msg_head(self):
        """CurrentPacket.EventData.MsgHead"""
        return c(self, "msg_head", self.model.CurrentPacket.EventData.MsgHead)

    @property
    def msg_body(self):
        """CurrentPacket.EventData.MsgBody"""
        return c(self, "msg_body", self.model.CurrentPacket.EventData.MsgBody)

    @property
    def from_group(self) -> int:
        """群ID"""
        # TODO: GroupInfo 有时候没有，需要确认
        return c(self, "from_group", self.msg_head.GroupInfo.GroupCode)  # type: ignore

    @property
    def images(self):
        """图片列表 可能为None"""
        return c(self, "images", self.msg_body.Images)

    @property
    def voice(self):
        """语音 可能为None"""
        return c(self, "voice", self.msg_body.Voice)

    @property
    def video(self):
        """短视频 可能为None"""
        return c(self, "video", self.msg_body.Video)

    @property
    def at_list(self):
        """被艾特列表 注意不是int列表"""
        return c(self, "at_list", self.msg_body.AtUinLists or [])

    @property
    def text(self):
        """文字内容"""
        return c(self, "text", self.msg_body.Content)

    def is_at_user(self, user_id: int):
        """是否艾特某人"""
        return user_id in (i.QQUid for i in self.at_list or [])

    @property
    def is_at_bot(self):
        """是否艾特机器人"""
        return c(self, "is_at_bot", self.is_at_user(self.model.CurrentQQ))

    @property
    def is_from_self(self):
        """是否来自机器人自身"""
        return c(
            self,
            "is_from_self",
            self.model.CurrentQQ == self.msg_head.SenderUin,
        )

    @property
    def sender_uin(self):
        """发送者qq号"""
        return c(self, "sender_uin", self.msg_head.SenderUin)

    @property
    def sender_nick(self):
        """发送者昵称"""
        return c(self, "sender_nick", self.msg_head.SenderNick)


class FriendMsg:
    def __init__(self, data):
        model = models.FriendMsg.parse_raw(data)  # type: ignore
        self.model = model


class EventMsg:
    def __init__(self, data):
        model = models.EventMsg.parse_raw(data)  # type: ignore
        self.model = model


class Context:
    def __init__(self, data: str) -> None:
        """
        :param data: websokets收到的原始包数据
        """
        self.__data = data

    @property
    def data(self) -> str:
        """websokets收到的原始包数据"""
        return self.__data

    @property
    def group_msg(self) -> Optional[GroupMsg]:
        msg = None
        try:
            msg = GroupMsg(self.__data)
        except Exception:
            print(traceback.format_exc())
        return c(self, "group_msg", msg)

    @property
    def friend_msg(self) -> Optional[FriendMsg]:
        msg = None
        try:
            msg = FriendMsg(self.__data)
        except Exception:
            pass
        return c(self, "friend_msg", msg)

    @property
    def event_msg(self) -> Optional[EventMsg]:
        msg = None
        try:
            msg = EventMsg(self.__data)
        except Exception:
            pass
        return c(self, "event_msg", msg)


ctx_var: ContextVar[Context] = ContextVar("ctx")
ctx: Context = bind_contextvar(ctx_var)  # type: ignore
