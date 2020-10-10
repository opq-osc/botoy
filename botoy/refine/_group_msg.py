# pylint: disable=R0902,W0231
from typing import List

from botoy import json
from botoy.collection import MsgTypes
from botoy.exceptions import InvalidContextError
from botoy.model import GroupMsg
from botoy.refine import _copy_ctx


class _GroupMsg(GroupMsg):
    def _carry_properties(self, ctx: GroupMsg):
        self.message = ctx.message
        self.CurrentQQ = ctx.CurrentQQ

        self.data = ctx.data

        self.FromGroupId: int = ctx.FromGroupId
        self.FromGroupName: str = ctx.FromGroupId
        self.FromUserId: int = ctx.FromUserId
        self.FromNickName: str = ctx.FromNickName
        self.Content: str = ctx.Content
        self.MsgType: str = ctx.MsgType
        self.MsgTime: int = ctx.MsgTime
        self.MsgSeq: int = ctx.MsgSeq
        self.MsgRandom: int = ctx.MsgRandom
        self.RedBaginfo: dict = ctx.RedBaginfo


class _VoiceGroupMsg(_GroupMsg):
    """群语音消息"""

    def __init__(self, ctx: GroupMsg):
        voice_data = json.loads(ctx.Content)
        self.VoiceUrl: str = voice_data['Url']
        self.Tips: str = voice_data['Tips']
        super()._carry_properties(ctx)


class _VideoGroupMsg(_GroupMsg):
    """群视频消息"""

    def __init__(self, ctx: GroupMsg):
        video_data = json.loads(ctx.Content)
        self.ForwordBuf: str = video_data['ForwordBuf']
        self.ForwordField: int = video_data['ForwordField']
        self.Tips: str = video_data['Tips']
        self.VideoMd5: str = video_data['VideoMd5']
        self.VideoSize: str = video_data['VideoSize']
        self.VideoUrl: str = video_data['VideoUrl']
        super()._carry_properties(ctx)


class _GroupPic:
    def __init__(self, pic: dict):
        '''[{"FileId":2161733733,"FileMd5":"","FileSize":449416,"ForwordBuf":"","ForwordField":8,"Url":""}'''
        self.FileId: int = pic.get('FileId')
        self.FileMd5: str = pic.get('FileMd5')
        self.FileSize: int = pic.get('FileSize')
        self.ForwordBuf: str = pic.get('ForwordBuf')
        self.ForwordField: int = pic.get('ForwordField')
        self.Url: str = pic.get('Url')


class _PicGroupMsg(_GroupMsg):
    """群图片/表情包消息"""

    def __init__(self, ctx: GroupMsg):
        pic_data = json.loads(ctx.Content)
        self.GroupPic: List[_GroupPic] = [_GroupPic(i) for i in pic_data['GroupPic']]
        self.Tips: str = pic_data['Tips']
        super()._carry_properties(ctx)
        self.Content: str = pic_data.get('Content')


class _AtGroupMsg(_GroupMsg):
    def __init__(self, ctx: GroupMsg):
        super()._carry_properties(ctx)
        # TODO:


class _RedBagGroupMsg(_GroupMsg):
    """群红包消息"""

    def __init__(self, ctx: GroupMsg):
        redbag_info = ctx.RedBaginfo
        self.RedBag_Authkey: str = redbag_info.get('Authkey')
        self.RedBag_Channel: int = redbag_info.get('Channel')
        self.RedBag_Des: str = redbag_info.get('Des')
        self.RedBag_FromType: int = redbag_info.get('FromType')
        self.RedBag_FromUin: int = redbag_info.get('FromUin')
        self.RedBag_Listid: str = redbag_info.get('Listid')
        self.RedBag_RedType: int = redbag_info.get('RedType')
        self.RedBag_StingIndex: str = redbag_info.get('StingIndex')
        self.RedBag_Tittle: str = redbag_info.get('Tittle')
        self.RedBag_Token_17_2: str = redbag_info.get('Token_17_2')
        self.RedBag_Token_17_3: str = redbag_info.get('Token_17_3')
        super()._carry_properties(ctx)


@_copy_ctx
def refine_voice_group_msg(ctx: GroupMsg) -> _VoiceGroupMsg:
    """群语音消息"""
    if not isinstance(ctx, GroupMsg):
        raise InvalidContextError('Expected `GroupMsg`, but got `%s`' % ctx.__class__)
    if ctx.MsgType == MsgTypes.VoiceMsg:
        return _VoiceGroupMsg(ctx)
    return None


@_copy_ctx
def refine_video_group_msg(ctx: GroupMsg) -> _VideoGroupMsg:
    """群视频消息"""
    if not isinstance(ctx, GroupMsg):
        raise InvalidContextError('Expected `GroupMsg`, but got `%s`' % ctx.__class__)
    if ctx.MsgType == MsgTypes.VideoMsg:
        return _VideoGroupMsg(ctx)
    return None


@_copy_ctx
def refine_pic_group_msg(ctx: GroupMsg) -> _PicGroupMsg:
    """群图片/表情包消息"""
    if not isinstance(ctx, GroupMsg):
        raise InvalidContextError('Expected `GroupMsg`, but got `%s`' % ctx.__class__)
    if ctx.MsgType == MsgTypes.PicMsg:
        return _PicGroupMsg(ctx)
    return None


@_copy_ctx
def refine_RedBag_group_msg(ctx: GroupMsg) -> _RedBagGroupMsg:
    """群红包消息"""
    if not isinstance(ctx, GroupMsg):
        raise InvalidContextError('Expected `GroupMsg`, but got `%s`' % ctx.__class__)
    if ctx.MsgType == MsgTypes.RedBagMsg:
        return _RedBagGroupMsg(ctx)
    return None
