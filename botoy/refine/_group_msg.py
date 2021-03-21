# pylint: disable=R0902,W0231
from typing import Dict, List

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
        self.FromGroupName: str = ctx.FromGroupName
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


class _ReplyGroupMsg(_GroupMsg):
    """群回复消息"""

    def __init__(self, ctx: GroupMsg):
        reply_data: Dict = json.loads(ctx.Content)
        super()._carry_properties(ctx)
        self.Content: str = reply_data.get('Content', '')
        self.OriginMsgSeq: int = reply_data.get('MsgSeq', -1)
        self.ReplyContent: str = reply_data.get('ReplayContent', '')
        self.SrcContent: str = reply_data.get('SrcContent', '')
        self.Tips: str = reply_data.get('Tips', '')
        self.AtUserID: List = reply_data.get('UserID', [])


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
        judge = {'[群图片]': 'GroupPic', '[好友图片]': 'FriendPic'}
        pic_data = json.loads(ctx.Content)
        self.Tips: str = pic_data['Tips']
        if self.Tips != '[群消息-QQ闪照]':
            self.GroupPic: List[_GroupPic] = [
                _GroupPic(i) for i in pic_data[judge[self.Tips]]
            ]
        else:
            self.GroupPic: List[_GroupPic] = [_GroupPic(pic_data)]
        super()._carry_properties(ctx)
        self.Content: str = pic_data.get('Content') or ''


class _AtGroupMsg(_GroupMsg):
    def __init__(self, ctx: GroupMsg):
        at_data: Dict = json.loads(ctx.Content)
        super()._carry_properties(ctx)
        self.Content: str = at_data.get('Content', '')
        self.OriginMsgSeq: int = at_data.get('MsgSeq', -1)
        self.SrcContent: str = at_data.get('SrcContent', '')
        self.Tips: str = at_data.get('Tips', '')
        self.AtUserID: List = at_data.get('UserID', [])


class _GroupFileMsg(_GroupMsg):
    def __init__(self, ctx: GroupMsg):
        file_data: Dict = json.loads(ctx.Content)
        super()._carry_properties(ctx)
        self.FileID: str = file_data.get('FileID', '')
        self.FileName: str = file_data.get('FileName', '')
        self.FileSize: int = file_data.get('FileSize', -1)
        self.Tips: str = file_data.get('Tips', '')


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


@_copy_ctx
def refine_reply_group_msg(ctx: GroupMsg) -> _ReplyGroupMsg:
    """群回复消息"""
    if not isinstance(ctx, GroupMsg):
        raise InvalidContextError('Expected `GroupMsg`, but got `%s`' % ctx.__class__)
    if ctx.MsgType in (
        MsgTypes.ReplyMsg,
        MsgTypes.ReplyMsgA,
    ):  # Workaround for naming errors
        return _ReplyGroupMsg(ctx)
    return None


@_copy_ctx
def refine_at_group_msg(ctx: GroupMsg) -> _AtGroupMsg:
    """群回复消息"""
    if not isinstance(ctx, GroupMsg):
        raise InvalidContextError('Expected `GroupMsg`, but got `%s`' % ctx.__class__)
    if ctx.MsgType == MsgTypes.AtMsg:
        return _AtGroupMsg(ctx)
    return None


@_copy_ctx
def refine_file_group_msg(ctx: GroupMsg) -> _GroupFileMsg:
    """群文件消息"""
    if not isinstance(ctx, GroupMsg):
        raise InvalidContextError('Expected `GroupMsg`, but got `%s`' % ctx.__class__)
    if ctx.MsgType == MsgTypes.GroupFileMsg:
        return _GroupFileMsg(ctx)
    return None
