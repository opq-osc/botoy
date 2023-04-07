import json
import re
from typing import List, Optional

from pydantic import BaseModel

from ..collection import MsgTypes
from ..model import GroupMsg


# at
class UserExtItem(BaseModel):
    QQNick: str
    QQUid: int


class AT(BaseModel):
    Content: str
    UserExt: List[UserExtItem]
    UserID: List[int]


def at(ctx: GroupMsg, clean=True) -> Optional[AT]:
    """艾特@ AtMsg
    :param clean: 如果为``True``将会清除发送文字内容中包含的被AT用户的昵称
    """
    try:
        assert ctx.MsgType == MsgTypes.AtMsg

        ret = AT(**json.loads(ctx.Content))
        if clean:
            ret_dict = ret.dict()
            for user in ret.UserExt:
                ret_dict["Content"] = re.sub(
                    f"@{user.QQNick}\\s+", "", ret_dict["Content"]
                )
            ret = AT(**ret_dict)
        return ret
    except Exception:
        pass
    return None


# reply
class Reply(BaseModel):
    Content: str
    SrcContent: str
    MsgSeq: int
    UserID: List[int]
    Tips: str = "[回复]"


def reply(ctx: GroupMsg) -> Optional[Reply]:
    """回复 AtMsg"""
    try:
        assert ctx.MsgType == MsgTypes.AtMsg

        data = json.loads(ctx.Content)
        users = []
        for user in data["UserID"]:
            if user not in users:
                users.append(user)
        data["UserID"] = users
        return Reply(**data)
    except Exception:
        pass
    return None


# picture
class PicItem(BaseModel):
    FileId: int
    FileMd5: str
    FileSize: int
    ForwordBuf: str
    ForwordField: int
    Url: str


class Pic(BaseModel):
    GroupPic: List[PicItem]
    Content: str = ""
    Tips: str  # FIXME: 处理这类情况，但无法复现该消息 [好友图片]
    UserExt: Optional[List[UserExtItem]]  # 即使at，有图就是图片消息。。。
    UserID: Optional[List[int]]


def pic(ctx: GroupMsg) -> Optional[Pic]:
    """图片 PicMsg"""
    try:
        assert ctx.MsgType == MsgTypes.PicMsg

        return Pic(**json.loads(ctx.Content))
    except Exception:
        pass
    return None


# voice
class Voice(BaseModel):
    Url: str
    Tips: str = "语音"


def voice(ctx: GroupMsg) -> Optional[Voice]:
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


def video(ctx: GroupMsg) -> Optional[Video]:
    """视频 VideoMsg"""
    try:
        assert ctx.MsgType == MsgTypes.VideoMsg

        return Video(**json.loads(ctx.Content))
    except Exception:
        pass
    return None


# file
class File(BaseModel):
    FileID: str
    FileName: str
    FileSize: int
    Tips: str = "[群文件]"


def file(ctx: GroupMsg) -> Optional[File]:
    """文件 GroupFileMsg"""
    try:
        assert ctx.MsgType == MsgTypes.GroupFileMsg

        return File(**json.loads(ctx.Content))
    except Exception:
        pass
    return None
