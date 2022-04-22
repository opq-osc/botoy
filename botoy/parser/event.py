from typing import Optional

from pydantic import BaseModel

from ..collection import EventNames
from ..model import EventMsg

#  --------- group event ---------

# revoke
class GroupRevoke(BaseModel):
    AdminUserID: int
    GroupID: int
    MsgRandom: int
    MsgSeq: int
    UserID: int


def group_revoke(ctx: EventMsg) -> Optional[GroupRevoke]:
    """撤回"""
    try:
        assert ctx.EventName == EventNames.ON_EVENT_GROUP_REVOKE
        return GroupRevoke(**ctx.EventData)
    except Exception:
        return None


# user exit
class GroupExit(BaseModel):
    UserID: int


def group_exit(ctx: EventMsg) -> Optional[GroupExit]:
    """用户退群"""
    try:
        assert ctx.EventName == EventNames.ON_EVENT_GROUP_EXIT
        return GroupExit(**ctx.EventData)
    except Exception:
        return None


# user join
class GroupJoin(BaseModel):
    InviteUin: int
    UserID: int
    UserName: str


def group_join(ctx: EventMsg) -> Optional[GroupJoin]:
    """新用户进群"""
    try:
        assert ctx.EventName == EventNames.ON_EVENT_GROUP_JOIN
        return GroupJoin(**ctx.EventData)
    except Exception:
        return None


# shut up
class GroupShut(BaseModel):
    GroupID: int
    ShutTime: int
    UserID: int


def group_shut(ctx: EventMsg) -> Optional[GroupShut]:
    """群禁言"""
    try:
        assert ctx.EventName == EventNames.ON_EVENT_GROUP_SHUT
        return GroupShut(**ctx.EventData)
    except Exception:
        return None


# adimn
class GroupAdmin(BaseModel):
    Flag: int
    GroupID: int
    UserID: int


def group_admin(ctx: EventMsg) -> Optional[GroupAdmin]:
    """管理员变更"""
    try:
        assert ctx.EventName == EventNames.ON_EVENT_GROUP_ADMIN
        return GroupAdmin(**ctx.EventData)
    except Exception:
        return None


class GroupAdminsysnotify(BaseModel):
    Type: int  # 事件类型
    Seq: int  # seq 处理进群的时候需要用
    MsgTypeStr: str  # 消息类型
    MsgStatusStr: str  # 消息类型状态
    Who: int  # 触发消息的对象
    WhoName: str  # 触发消息的对象昵称
    GroupId: int  # 来自群
    GroupName: str  # 群名
    ActionUin: int  # 邀请人(处理人)
    ActionName: str  # 邀请人(处理人)昵称
    ActionGroupCard: str  # 邀请人(处理人)群名片
    Action: str  # 加群理由 11 agree 14 忽略 12/21 disagree
    Content: str
    Flag_7: int
    Flag_8: int


def group_adminsysnotify(ctx: EventMsg) -> Optional[GroupAdminsysnotify]:
    """加群申请"""
    try:
        assert ctx.EventName == EventNames.ON_EVENT_GROUP_ADMINSYSNOTIFY
        return GroupAdminsysnotify(**ctx.EventData)
    except Exception:
        return None


# ------------ friend event ------------


# revoke
class FriendRevoke(BaseModel):
    MsgSeq: int
    UserID: int


def friend_revoke(ctx: EventMsg) -> Optional[FriendRevoke]:
    try:
        assert ctx.EventName == EventNames.ON_EVENT_FRIEND_DELETE
        return FriendRevoke(**ctx.EventData)
    except Exception:
        return None


# delete
class FriendDelete(BaseModel):
    UserID: int


def friend_delete(ctx: EventMsg) -> Optional[FriendDelete]:
    try:
        assert ctx.EventName == EventNames.ON_EVENT_FRIEND_DELETE
        return FriendDelete(**ctx.EventData)
    except Exception:
        return None


class FriendAdd(BaseModel):
    UserID: int
    UserNick: str
    FromType: int
    Type: int
    MsgTypeStr: str
    Field_3: int
    Field_8: int
    Content: str
    FromContent: str
    FromGroupId: int
    FromGroupName: str
    Action: int


def friend_add(ctx: EventMsg) -> Optional[FriendAdd]:
    try:
        assert ctx.EventName == EventNames.ON_EVENT_FRIEND_ADD
        return FriendAdd(**ctx.EventData)
    except Exception:
        return None
