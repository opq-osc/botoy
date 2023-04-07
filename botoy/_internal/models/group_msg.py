# generated by datamodel-codegen:
#   filename:  group_msg.json
#   timestamp: 2023-04-07T08:44:03+00:00

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class GroupInfo(BaseModel):
    GroupCard: Optional[str] = None
    GroupCode: Optional[int] = None
    GroupInfoSeq: Optional[int] = None
    GroupLevel: Optional[int] = None
    GroupRank: Optional[int] = None
    GroupType: Optional[int] = None
    GroupName: Optional[str] = None


class MsgHead(BaseModel):
    FromUin: Optional[int] = None
    ToUin: Optional[int] = None
    FromType: Optional[int] = None
    SenderUin: Optional[int] = None
    SenderNick: Optional[str] = None
    MsgType: Optional[int] = None
    C2cCmd: Optional[int] = None
    MsgSeq: Optional[int] = None
    MsgTime: Optional[int] = None
    MsgRandom: Optional[int] = None
    MsgUid: Optional[int] = None
    GroupInfo: Optional[GroupInfo] = None
    C2CTempMessageHead: Optional[Any] = None


class Video(BaseModel):
    FileMd5: Optional[str] = None
    FileSize: Optional[int] = None
    Url: Optional[str] = None


class MsgBody(BaseModel):
    SubMsgType: Optional[int] = None
    Content: Optional[str] = None
    AtUinLists: Optional[Any] = None
    Images: Optional[Any] = None
    Video: Optional[Video] = None
    Voice: Optional[Any] = None


class GroupMsg(BaseModel):
    MsgHead: Optional[MsgHead] = None
    MsgBody: Optional[MsgBody] = None
