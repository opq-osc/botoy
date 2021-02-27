# pylint: disable=C0413
"""解析各类消息的详细字段, 所有操作不会影响原始消息上下文对象"""
import copy
import functools


def _copy_ctx(f):
    @functools.wraps(f)
    def i(ctx):
        return f(copy.deepcopy(ctx))

    return i


from ._event import (
    _FriendDeleteEventMsg,
    _FriendRevokeEventMsg,
    _GroupAdminEventMsg,
    _GroupAdminsysnotifyEventMsg,
    _GroupExitEventMsg,
    _GroupJoinEventMsg,
    _GroupRevokeEventMsg,
    _GroupShutEventMsg,
    refine_friend_delete_event_msg,
    refine_friend_revoke_event_msg,
    refine_group_admin_event_msg,
    refine_group_adminsysnotify_event_msg,
    refine_group_exit_event_msg,
    refine_group_join_event_msg,
    refine_group_revoke_event_msg,
    refine_group_shut_event_msg
)
from ._friend_msg import (
    _FriendFileMsg,
    _FriendPic,
    _PicFriendMsg,
    _RedBagFriendMsg,
    _ReplyFriendMsg,
    _VideoFriendMsg,
    _VoiceFriendMsg,
    refine_file_friend_msg,
    refine_pic_friend_msg,
    refine_RedBag_friend_msg,
    refine_reply_friend_msg,
    refine_video_friend_msg,
    refine_voice_friend_msg
)
from ._group_msg import (
    _AtGroupMsg,
    _GroupFileMsg,
    _GroupPic,
    _PicGroupMsg,
    _RedBagGroupMsg,
    _ReplyGroupMsg,
    _VideoGroupMsg,
    _VoiceGroupMsg,
    refine_at_group_msg,
    refine_file_group_msg,
    refine_pic_group_msg,
    refine_RedBag_group_msg,
    refine_reply_group_msg,
    refine_video_group_msg,
    refine_voice_group_msg
)
