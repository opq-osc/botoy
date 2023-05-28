import json
import re
import traceback
from abc import ABCMeta, abstractmethod
from contextvars import ContextVar
from typing import Optional, Union

from . import action, models
from .log import logger
from .utils import bind_contextvar


def c(obj, key, value):  # c => cache
    obj.__dict__[key] = value
    return value


class BaseMsg(metaclass=ABCMeta):
    @property
    @abstractmethod
    def model(self) -> Union[models.GroupMsg, models.FriendMsg]:
        """数据包结构"""
        ...

    @property
    def msg_head(self):
        """CurrentPacket.EventData.MsgHead"""
        return c(self, "msg_head", self.model.CurrentPacket.EventData.MsgHead)

    @property
    def msg_body(self):
        """CurrentPacket.EventData.MsgBody"""
        return c(self, "msg_body", self.model.CurrentPacket.EventData.MsgBody)

    @property
    def images(self):
        """图片列表 可能为None"""
        return c(self, "images", self.msg_body.Images)  # type:ignore

    @property
    def voice(self):
        """语音 可能为None"""
        return c(self, "voice", self.msg_body.Voice)  # type:ignore

    @property
    def video(self):
        """短视频 可能为None"""
        return c(self, "video", self.msg_body.Video)  # type:ignore

    @property
    def text(self):
        """文字内容"""
        return c(self, "text", self.msg_body.Content)  # type:ignore

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

    @property
    def msg_random(self):
        """CurrentPacket.EventData.MsgHead.MsgRandom"""
        return c(self, "msg_random", self.msg_head.MsgRandom)

    @property
    def msg_seq(self):
        """CurrentPacket.EventData.MsgHead.MsgSeq"""
        return c(self, "msg_seq", self.msg_head.MsgSeq)

    @property
    def msg_time(self):
        """CurrentPacket.EventData.MsgHead.MsgTime"""
        return c(self, "msg_time", self.msg_head.MsgTime)

    @property
    def msg_uid(self):
        """CurrentPacket.EventData.MsgHead.MsgUid"""
        return c(self, "msg_uid", self.msg_head.MsgUid)

    @property
    def msg_type(self):
        """CurrentPacket.EventData.MsgHead.MsgType"""
        return c(self, "msg_type", self.msg_head.MsgType)

    @property
    def from_type(self):
        """CurrentPacket.EventData.MsgHead.FromType"""
        return c(self, "from_type", self.msg_head.FromType)

    @property
    def bot_qq(self):
        """机器人qq"""
        return c(self, "bot_qq", self.model.CurrentQQ)

    def text_match(self, pattern: Union[str, re.Pattern]):
        """等于 re.match(pattern, text)"""
        return re.match(pattern, self.text)

    def __repr__(self) -> str:
        return "{cls} => {data}".format(
            cls=self.__class__.__name__, data=str(self.model)
        )


class GroupMsg(BaseMsg):
    def __init__(self, data: Union[str, dict]):
        super().__init__()
        if isinstance(data, str):
            model = models.GroupMsg.parse_raw(data)
        else:
            model = models.GroupMsg(**data)

        assert (
            model.CurrentPacket.EventData.MsgHead.C2cCmd
            == model.CurrentPacket.EventData.MsgHead.C2cCmd.integer_0
        ), "GroupMsg: C2cCmd == 0"

        assert (
            model.CurrentPacket.EventName
            == model.CurrentPacket.EventName.ON_EVENT_GROUP_NEW_MSG
        ), "GroupMsg: EventName == ON_EVENT_GROUP_NEW_MSG"

        self.__model = model

    @property
    def model(self) -> models.GroupMsg:
        return self.__model

    @property
    def from_group(self) -> int:
        """群ID"""
        return c(self, "from_group", self.msg_head.FromUin)

    @property
    def from_group_name(self) -> str:
        """群名称"""
        return c(
            self, "from_group_name", self.msg_head.GroupInfo.GroupName  # type:ignore
        )

    @property
    def from_user(self) -> int:
        """发送者"""
        return c(self, "from_user", self.msg_head.SenderUin)

    @property
    def from_user_name(self) -> str:
        """发送者昵称"""
        return c(self, "from_user_name", self.msg_head.SenderNick)

    @property
    def at_list(self):
        """被艾特列表 注意不是int列表"""
        return c(self, "at_list", self.msg_body.AtUinLists or [])  # type:ignore

    def is_at_user(self, user_id: int):
        """是否艾特某人"""
        return user_id in (i.Uin for i in self.at_list or [])

    @property
    def is_at_bot(self):
        """是否艾特机器人"""
        return c(self, "is_at_bot", self.is_at_user(self.model.CurrentQQ))

    async def revoke(self):
        """撤回该消息"""
        async with action.Action(self.bot_qq) as a:
            return await a.revoke(self)


class FriendMsg(BaseMsg):
    def __init__(self, data: Union[str, dict]):
        super().__init__()
        if isinstance(data, str):
            model = models.FriendMsg.parse_raw(data)
        else:
            model = models.FriendMsg(**data)

        assert (
            model.CurrentPacket.EventData.MsgHead.C2cCmd
            == model.CurrentPacket.EventData.MsgHead.C2cCmd.integer_11
        ), "FriendMsg: C2cCmd == 11"

        assert (
            model.CurrentPacket.EventName
            == model.CurrentPacket.EventName.ON_EVENT_FRIEND_NEW_MSG
        ), "FriendMsg: EventName == ON_EVENT_FRIEND_NEW_MSG"

        self.__model = model

    @property
    def model(self) -> models.FriendMsg:
        return self.__model

    @property
    def from_user(self) -> int:
        """发送者qq"""
        return c(self, "from_user", self.msg_head.FromUin)

    @property
    def from_user_name(self) -> str:
        """发送者昵称"""
        return c(self, "from_user_name", self.msg_head.SenderNick)

    @property
    def is_private(self) -> bool:
        """是否为私聊"""
        try:
            self.from_group
        except Exception:
            return False
        else:
            return True

    @property
    def from_group(self) -> int:
        """发送者群号, 私聊才有，如果非私聊进行调用会报错"""
        assert self.msg_head.C2CTempMessageHead is not None
        return c(self, "from_group", self.msg_head.C2CTempMessageHead.GroupCode)

    @property
    def is_from_phone(self):
        return c(
            self,
            "if_from_phone",
            # NOTE: 来自手机MsgBody为空，但这种场景用得太少, 其他方法中
            # 如果考虑msg_body为空的话，逻辑会增加不少
            self.msg_body is None and self.msg_head.FromUin == self.msg_head.ToUin
            # TODO: 用枚举
            and self.msg_type == 529,
        )


class EventMsg:
    def __init__(self, data):
        model = models.EventMsg.parse_raw(data)  # type: ignore
        self.model = model


class Context:
    def __init__(self, data: Union[str, dict]) -> None:
        """
        :param data: websokets收到的原始包数据
        """
        if isinstance(data, dict):
            self.__data = data
        else:
            self.__data = json.loads(data)

    @property
    def data(self) -> dict:
        """websokets收到的原始包数据"""
        return self.__data

    @property
    def bot_qq(self) -> int:
        """当前机器人QQ"""
        return self.data["CurrentQQ"]  # type: ignore

    @property
    def group_msg(self) -> Optional[GroupMsg]:
        msg = None
        try:
            msg = GroupMsg(self.__data)
        except Exception:
            logger.debug(f"filter message: {traceback.format_exc()}")

        return c(self, "group_msg", msg)

    @property
    def g(self) -> Optional[GroupMsg]:
        return self.group_msg

    @property
    def friend_msg(self) -> Optional[FriendMsg]:
        msg = None
        try:
            msg = FriendMsg(self.__data)
        except Exception:
            logger.debug(f"filter message: {traceback.format_exc()}")
        return c(self, "friend_msg", msg)

    @property
    def f(self) -> Optional[FriendMsg]:
        return self.friend_msg

    @property
    def event_msg(self) -> Optional[EventMsg]:
        raise NotImplementedError
        msg = None
        try:
            msg = EventMsg(self.__data)
        except AssertionError:
            pass
        except:
            logger.warning("收到该错误，请进行反馈!\n" + traceback.format_exc())
        return c(self, "event_msg", msg)

    @property
    def e(self) -> Optional[EventMsg]:
        return self.event_msg

    def __repr__(self) -> str:
        return "Context => {data}".format(data=str(self.data))


current_ctx: ContextVar[Context] = ContextVar("ctx")
ctx: Context = bind_contextvar(current_ctx)  # type: ignore
