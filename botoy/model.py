# pylint: disable=too-many-instance-attributes
from typing import Optional


class GroupMsg:
    message: dict  # raw message
    CurrentQQ: int  # bot qq
    data: dict  # Data
    # data items
    FromGroupId: int
    FromGroupName: str
    FromUserId: int
    FromNickName: str
    Content: str
    MsgType: str
    MsgTime: int
    MsgSeq: int
    MsgRandom: int
    RedBaginfo: Optional[dict]

    def __init__(self, message: dict):
        data = message["CurrentPacket"]["Data"]

        # basic
        for name, value in dict(
            message=message,
            CurrentQQ=message["CurrentQQ"],
            data=data,
        ).items():
            self.__setattr__(name, value)

        # set Data items
        for name in [
            "FromGroupId",
            "FromGroupName",
            "FromUserId",
            "FromNickName",
            "Content",
            "MsgType",
            "MsgTime",
            "MsgSeq",
            "MsgRandom",
            "RedBaginfo",
        ]:
            self.__setattr__(name, data.get(name))

    def __repr__(self):
        return f"GroupMsg => {self.data}"


class FriendMsg:
    message: dict  # raw message
    CurrentQQ: int  # bot qq
    data: dict  # Data
    # data items
    FromUin: int
    ToUin: int
    Content: str
    MsgType: str
    MsgSeq: int
    TempUin: int  # 私聊(临时会话)特有, 入口群聊ID
    RedBaginfo: Optional[dict]

    def __init__(self, message: dict):
        data = message["CurrentPacket"]["Data"]

        # basic
        for name, value in dict(
            message=message,
            CurrentQQ=message["CurrentQQ"],
            data=data,
        ).items():
            self.__setattr__(name, value)

        # set Data items
        for name in [
            "FromUin",
            "ToUin",
            "Content",
            "MsgType",
            "MsgSeq",
            "RedBaginfo",
            "TempUin",
        ]:
            self.__setattr__(name, data.get(name))

    def __repr__(self):
        return f"FriendMsg => {self.data}"


class EventMsg:
    message: dict  # raw message
    CurrentQQ: int  # bot qq
    data: dict  # Data
    # Data items
    EventName: str
    EventData: dict
    EventMsg: dict
    # EventMsg items
    Content: str
    FromUin: int
    MsgSeq: int
    MsgType: str
    ToUin: int
    RedBaginfo: Optional[dict]

    def __init__(self, message: dict):
        data = message["CurrentPacket"]["Data"]

        # basic
        for name, value in dict(
            message=message,
            CurrentQQ=message["CurrentQQ"],
            data=data,
        ).items():
            self.__setattr__(name, value)

        # set Data items
        for name in ["EventName", "EventData", "EventMsg"]:
            self.__setattr__(name, data.get(name))
        # set EventMsg items
        eventMsg = data["EventMsg"]
        for name in ["Content", "FromUin", "MsgSeq", "MsgType", "ToUin", "RedBaginfo"]:
            self.__setattr__(name, eventMsg.get(name))

    def __repr__(self):
        return f"EventMsg => {self.data}"
