# generated by datamodel-codegen:
#   filename:  group_msg.json
#   timestamp: 2023-04-15T09:46:55+00:00

from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class FromType(Enum):
    integer_1 = 1
    integer_2 = 2
    integer_3 = 3


class C2cCmd(Enum):
    integer_0 = 0
    integer_1 = 1
    integer_17 = 17
    integer_349 = 349
    integer_20 = 20
    integer_212 = 212
    integer_8 = 8
    integer_11 = 11


class GroupInfo(BaseModel):
    GroupCard: str
    GroupCode: int
    GroupInfoSeq: int
    GroupLevel: int
    GroupRank: int
    GroupType: int
    GroupName: str


class MsgHead(BaseModel):
    FromUin: int
    ToUin: int
    FromType: FromType = Field(..., description="消息来源类型 3私聊 2群组 1好友")
    SenderUin: int = Field(..., description="发送者QQ号")
    SenderNick: str
    MsgType: int
    C2cCmd: C2cCmd = Field(
        ...,
        description="0 收到群消息, 1 发出去消息的回应, 17 群消息被撤回, 349 上下线, 20 被拉群， 212 群解散， 8 上线， 11 好友私聊",
    )
    MsgSeq: int
    MsgTime: int
    MsgRandom: int
    MsgUid: int
    GroupInfo: Optional[GroupInfo] = None
    C2CTempMessageHead: Optional[Any] = None


class AtUinList(BaseModel):
    Nick: str
    Uin: int


class Image(BaseModel):
    FileId: int
    FileMd5: str
    FileSize: int
    Url: str


class Video(BaseModel):
    FileMd5: str
    FileSize: int
    Url: str


class Voice(BaseModel):
    FileMd5: str
    FileSize: int
    Url: str


class MsgBody(BaseModel):
    SubMsgType: int = Field(
        ..., description="0为单一或复合类型消息(文字 At 图片 自由组合), 12 Xml消息 19 Video消息 51 JSON卡片消息"
    )
    Content: str
    AtUinLists: Optional[List[AtUinList]] = None
    Images: Optional[List[Image]] = None
    Video: Optional[Video] = None
    Voice: Optional[Voice] = None


class EventData(BaseModel):
    MsgHead: MsgHead
    MsgBody: MsgBody


class EventName(Enum):
    ON_EVENT_QQNT_NEW_MSG = "ON_EVENT_QQNT_NEW_MSG"
    ON_EVENT_GROUP_NEW_MSG = "ON_EVENT_GROUP_NEW_MSG"


class CurrentPacket(BaseModel):
    EventData: EventData
    EventName: EventName


class GroupMsg(BaseModel):
    CurrentPacket: CurrentPacket
    CurrentQQ: int = Field(..., description="Bot QQ号")
