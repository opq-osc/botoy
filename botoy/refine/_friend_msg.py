# pylint: disable=R0902,W0231
import json
from typing import Dict, List

from botoy.collection import MsgTypes
from botoy.exceptions import InvalidContextError
from botoy.model import FriendMsg
from botoy.refine import _copy_ctx


class _FriendMsg(FriendMsg):
    def _carry_properties(self, ctx: FriendMsg):
        self.message = ctx.message
        self.CurrentQQ = ctx.CurrentQQ

        self.data = ctx.data

        self.FromUin: int = ctx.FromUin
        self.ToUin: int = ctx.ToUin
        self.MsgType: str = ctx.MsgType
        self.MsgSeq: int = ctx.MsgSeq
        self.Content: str = ctx.Content
        self.RedBaginfo: dict = ctx.RedBaginfo


class _VoiceFriendMsg(_FriendMsg):
    """好友语音消息"""

    def __init__(self, ctx: FriendMsg):
        voice_data = json.loads(ctx.Content)
        self.VoiceUrl: str = voice_data["Url"]
        self.Tips: str = voice_data["Tips"]
        super()._carry_properties(ctx)


class _VideoFriendMsg(_FriendMsg):
    """好友视频消息"""

    def __init__(self, ctx: FriendMsg):
        video_data = json.loads(ctx.Content)
        self.ForwordBuf: str = video_data["ForwordBuf"]
        self.ForwordField: int = video_data["ForwordField"]
        self.Tips: str = video_data["Tips"]
        self.VideoMd5: str = video_data["VideoMd5"]
        self.VideoSize: str = video_data["VideoSize"]
        self.VideoUrl: str = video_data["VideoUrl"]
        super()._carry_properties(ctx)


class _FriendPic:
    def __init__(self, pic: dict):
        """好友图片单个图片所包含的数据
        [{"FileMd5":"","FileSize":0,"Path":"","Url":""}]中的一个
        """
        self.FileMd5: str = pic.get("FileMd5")
        self.FileSize: int = pic.get("FileSize")
        self.Path: str = pic.get("Path")
        self.Url: str = pic.get("Url")


class _PicFriendMsg(_FriendMsg):
    """好友图片/表情包消息"""

    def __init__(self, ctx: FriendMsg):
        pic_data = json.loads(ctx.Content)
        self.FriendPic: List[_FriendPic] = [
            _FriendPic(i) for i in pic_data["FriendPic"]
        ]
        self.Tips: str = pic_data["Tips"]
        super()._carry_properties(ctx)
        self.Content = pic_data.get("Content") or ""


class _RedBagFriendMsg(_FriendMsg):
    """好友红包消息"""

    def __init__(self, ctx: FriendMsg):
        redbag_info = ctx.RedBaginfo
        self.RedBag_Authkey: str = redbag_info.get("Authkey")
        self.RedBag_Channel: int = redbag_info.get("Channel")
        self.RedBag_Des: str = redbag_info.get("Des")
        self.RedBag_FromType: int = redbag_info.get("FromType")
        self.RedBag_FromUin: int = redbag_info.get("FromUin")
        self.RedBag_Listid: str = redbag_info.get("Listid")
        self.RedBag_RedType: int = redbag_info.get("RedType")
        self.RedBag_StingIndex: str = redbag_info.get("StingIndex")
        self.RedBag_Tittle: str = redbag_info.get("Tittle")
        self.RedBag_Token_17_2: str = redbag_info.get("Token_17_2")
        self.RedBag_Token_17_3: str = redbag_info.get("Token_17_3")
        super()._carry_properties(ctx)


class _ReplyFriendMsg(_FriendMsg):
    """好友语音消息"""

    def __init__(self, ctx: FriendMsg):
        reply_data: Dict = json.loads(ctx.Content)
        super()._carry_properties(ctx)
        self.Content: str = reply_data.get("Content", "")
        self.OriginMsgSeq: int = reply_data.get("MsgSeq", -1)
        self.SrcContent: str = reply_data.get("SrcContent", "")
        self.Tips: str = reply_data.get("Tips", "")
        self.AtUserID: List = reply_data.get("UserID", [])


class _FriendFileMsg(_FriendMsg):
    """好友文件消息"""

    def __init__(self, ctx: FriendMsg):
        file_data: Dict = json.loads(ctx.Content)
        super()._carry_properties(ctx)
        self.FileID: str = file_data.get("FileID", "")
        self.FileName: str = file_data.get("FileName", "")
        self.FileSize: int = file_data.get("FileSize", -1)
        self.Tips: str = file_data.get("Tips", "")


@_copy_ctx
def refine_voice_friend_msg(ctx: FriendMsg) -> _VoiceFriendMsg:
    """好友语音消息"""
    if not isinstance(ctx, FriendMsg):
        raise InvalidContextError("Expected `FriendMsg`, but got `%s`" % ctx.__class__)
    if ctx.MsgType == MsgTypes.VoiceMsg:
        return _VoiceFriendMsg(ctx)
    return None


@_copy_ctx
def refine_video_friend_msg(ctx: FriendMsg) -> _VideoFriendMsg:
    """好友视频消息"""
    if not isinstance(ctx, FriendMsg):
        raise InvalidContextError("Expected `FriendMsg`, but got `%s`" % ctx.__class__)
    if ctx.MsgType == MsgTypes.VideoMsg:
        return _VideoFriendMsg(ctx)
    return None


@_copy_ctx
def refine_pic_friend_msg(ctx: FriendMsg) -> _PicFriendMsg:
    """好友图片/表情包消息"""
    if not isinstance(ctx, FriendMsg):
        raise InvalidContextError("Expected `FriendMsg`, but got `%s`" % ctx.__class__)
    if ctx.MsgType == MsgTypes.PicMsg:
        return _PicFriendMsg(ctx)
    return None


@_copy_ctx
def refine_RedBag_friend_msg(ctx: FriendMsg) -> _RedBagFriendMsg:
    """好友红包消息"""
    if not isinstance(ctx, FriendMsg):
        raise InvalidContextError("Expected `FriendMsg`, but got `%s`" % ctx.__class__)
    if ctx.MsgType == MsgTypes.RedBagMsg:
        return _RedBagFriendMsg(ctx)
    return None


@_copy_ctx
def refine_reply_friend_msg(ctx: FriendMsg) -> _ReplyFriendMsg:
    """好友回复消息"""
    if not isinstance(ctx, FriendMsg):
        raise InvalidContextError("Expected `FriendMsg`, but got `%s`" % ctx.__class__)
    if ctx.MsgType in (MsgTypes.ReplyMsg, MsgTypes.ReplyMsgA):
        return _ReplyFriendMsg(ctx)
    return None


@_copy_ctx
def refine_file_friend_msg(ctx: FriendMsg) -> _FriendFileMsg:
    """好友文件消息"""
    if not isinstance(ctx, FriendMsg):
        raise InvalidContextError("Expected `FriendMsg`, but got `%s`" % ctx.__class__)
    if ctx.MsgType == MsgTypes.FriendFileMsg:
        return _FriendFileMsg(ctx)
    return None
