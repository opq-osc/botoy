import json
from typing import List, Optional

from pydantic import BaseModel

from ..collection import MsgTypes
from ..model import FriendMsg


# pic
class PicItem(BaseModel):
    FileMd5: str
    FileSize: int
    Path: str
    Url: str


class Pic(BaseModel):
    FriendPic: List[PicItem]
    Tips: str
    Content: str = ""


def pic(ctx: FriendMsg) -> Optional[Pic]:
    """图片 PicMsg"""
    try:
        assert ctx.MsgType == MsgTypes.PicMsg

        return Pic(**json.loads(ctx.Content))
    except Exception:
        pass
    return None


# voice
class Voice(BaseModel):
    VoiceUrl: str
    Tips: str


def voice(ctx: FriendMsg) -> Optional[Voice]:
    """语音 VoiceMsg"""
    try:
        assert ctx.MsgType == MsgTypes.VoiceMsg

        return Voice(**json.loads(ctx.Content))
    except Exception:
        pass
    return None


# video
class Video(BaseModel):
    ForwordBuf: str
    ForwordField: int
    VideoMd5: str
    VideoSize: str
    VideoUrl: str
    Tips: str


def video(ctx: FriendMsg) -> Optional[Video]:
    """视频 VideoMsg"""
    try:
        assert ctx.MsgType == MsgTypes.VideoMsg

        return Video(**json.loads(ctx.Content))
    except Exception:
        pass
    return None


# reply
class Reply(BaseModel):
    Content: str
    MsgSeq: int
    SrcContent: str
    UserID: List[int]
    Tips: str


def reply(ctx: FriendMsg) -> Optional[Reply]:
    """回复 ReplayMsg"""
    try:
        assert ctx.MsgType in (MsgTypes.ReplyMsg, MsgTypes.ReplyMsgA)

        return Reply(**json.loads(ctx.Content))
    except Exception:
        pass
    return None


# file
class File(BaseModel):
    FileID: str
    FileName: str
    FileSize: int
    Tips: str = "[好友文件]"


def file(ctx: FriendMsg) -> Optional[File]:
    """文件 FriendFileMsg"""
    try:
        assert ctx.MsgType == MsgTypes.FriendFileMsg

        return File(**json.loads(ctx.Content))
    except Exception:
        pass
    return None
