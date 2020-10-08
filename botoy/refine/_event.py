# pylint: disable=R0902,W0231
from botoy.collection import EventNames
from botoy.exceptions import InvalidContextError
from botoy.model import EventMsg
from botoy.refine import _copy_ctx


class _EventMsg(EventMsg):
    def _carry_properties(self, ctx: EventMsg):
        self.message = ctx.message
        self.CurrentQQ = ctx.CurrentQQ

        self.data = ctx.data

        self.EventName = ctx.EventName
        self.EventData = ctx.EventData
        self.EventMsg = ctx.EventMsg

        self.Content = ctx.Content
        self.FromUin = ctx.FromUin
        self.MsgSeq = ctx.MsgSeq
        self.MsgType = ctx.MsgType
        self.ToUin = ctx.ToUin
        self.RedBaginfo = ctx.RedBaginfo


class _GroupRevokeEventMsg(_EventMsg):
    """群成员撤回消息事件"""

    def __init__(self, ctx: EventMsg):
        event_data = ctx.EventData
        self.AdminUserID: int = event_data.get('AdminUserID')
        self.GroupID: int = event_data.get('GroupID')
        self.MsgRandom: int = event_data.get('MsgRandom')
        self.MsgSeq: int = event_data.get('MsgSeq')
        self.UserID: int = event_data.get('UserID')
        super()._carry_properties(ctx)


class _GroupExitEventMsg(_EventMsg):
    """群成员退出群聊事件"""

    def __init__(self, ctx: EventMsg):
        self.UserID = ctx.EventData.get('UserID')
        super()._carry_properties(ctx)


class _GroupJoinEventMsg(_EventMsg):
    """某人进群事件"""

    def __init__(self, ctx: EventMsg):
        e_data = ctx.EventData
        self.InviteUin: int = e_data.get('InviteUin')
        self.UserID: int = e_data.get('UserID')
        self.UserName: str = e_data.get('UserName')
        super()._carry_properties(ctx)


class _FriendRevokeEventMsg(_EventMsg):
    """好友撤回消息事件"""

    def __init__(self, ctx: EventMsg):
        self.MsgSeq = ctx.EventData.get('MsgSeq')
        self.UserID = ctx.EventData.get('UserID')
        super()._carry_properties(ctx)


class _FriendDeleteEventMsg(_EventMsg):
    """删除好友事件"""

    def __init__(self, ctx: EventMsg):
        self.UserID: int = ctx.EventData.get('UserID')
        super()._carry_properties(ctx)


class _GroupAdminsysnotifyEventMsg(_EventMsg):
    """QQ群系统消息通知(加群申请在这里面"""

    def __init__(self, ctx: EventMsg):
        edata = ctx.EventData
        self.Type: int = edata.get('Type')  # 事件类型
        self.MsgTypeStr: str = edata.get('MsgTypeStr')  # 消息类型
        self.MsgStatusStr: str = edata.get('MsgStatusStr')  # 消息类型状态
        self.Who: int = edata.get('Who')  # 触发消息的对象
        self.WhoName: int = edata.get('WhoName')  # 触发消息的对象昵称
        self.GroupID: int = edata.get('GroupId')  # 来自群
        self.GroupName: str = edata.get('GroupName')  # 群名
        self.ActionUin: int = edata.get('ActionUin')  # 邀请人(处理人)
        self.ActionName: str = edata.get('ActionName')  # 邀请人(处理人)昵称
        self.ActionGroupCard: str = edata.get('ActionGroupCard')  # 邀请人(处理人)群名片
        self.Action: str = edata.get('Action')  # 加群理由 11 agree 14 忽略 12/21 disagree
        self.Content: int = edata.get('Content')
        super()._carry_properties(ctx)


class _GroupShutEventMsg(_EventMsg):
    """群禁言事件"""

    def __init__(self, ctx: EventMsg):
        self.GroupID: int = ctx.EventData.get('GroupID')
        self.ShutTime: int = ctx.EventData.get('ShutTime')
        self.UserID: int = ctx.EventData.get('UserID')
        super()._carry_properties(ctx)


class _GroupAdminEventMsg(_EventMsg):
    """管理员变更事件"""

    def __init__(self, ctx: EventMsg):
        self.Flag: int = ctx.EventData.get('Flag')
        self.GroupID: int = ctx.EventData.get('GroupID')
        self.UserID: int = ctx.EventData.get('UserID')
        super()._carry_properties(ctx)


@_copy_ctx
def refine_group_revoke_event_msg(ctx: EventMsg) -> _GroupRevokeEventMsg:
    """群成员撤回消息事件"""
    if not isinstance(ctx, EventMsg):
        raise InvalidContextError('Expected `EventMsg`, but got `%s`' % ctx.__class__)
    if ctx.EventName == EventNames.ON_EVENT_GROUP_REVOKE:
        return _GroupRevokeEventMsg(ctx)
    return None


@_copy_ctx
def refine_group_exit_event_msg(ctx: EventMsg) -> _GroupExitEventMsg:
    """群成员退出群聊事件"""
    if not isinstance(ctx, EventMsg):
        raise InvalidContextError('Expected `EventMsg`, but got `%s`' % ctx.__class__)
    if ctx.EventName == EventNames.ON_EVENT_GROUP_EXIT:
        return _GroupExitEventMsg(ctx)
    return None


@_copy_ctx
def refine_group_join_event_msg(ctx: EventMsg) -> _GroupJoinEventMsg:
    """某人进群事件"""
    if not isinstance(ctx, EventMsg):
        raise InvalidContextError('Expected `EventMsg`, but got `%s`' % ctx.__class__)
    if ctx.EventName == EventNames.ON_EVENT_GROUP_JOIN:
        return _GroupJoinEventMsg(ctx)
    return None


@_copy_ctx
def refine_friend_revoke_event_msg(ctx: EventMsg) -> _FriendRevokeEventMsg:
    """好友撤回消息事件"""
    if not isinstance(ctx, EventMsg):
        raise InvalidContextError('Expected `EventMsg`, but got `%s`' % ctx.__class__)
    if ctx.EventName == EventNames.ON_EVENT_FRIEND_REVOKE:
        return _FriendRevokeEventMsg(ctx)
    return None


@_copy_ctx
def refine_friend_delete_event_msg(ctx: EventMsg) -> _FriendDeleteEventMsg:
    """删除好友事件"""
    if not isinstance(ctx, EventMsg):
        raise InvalidContextError('Expected `EventMsg`, but got `%s`' % ctx.__class__)
    if ctx.EventName == EventNames.ON_EVENT_FRIEND_DELETE:
        return _FriendDeleteEventMsg(ctx)
    return None


@_copy_ctx
def refine_group_adminsysnotify_event_msg(
    ctx: EventMsg,
) -> _GroupAdminsysnotifyEventMsg:
    """加群申请"""
    if not isinstance(ctx, EventMsg):
        raise InvalidContextError('Expected `EventMsg`, but got `%s`' % ctx.__class__)
    if ctx.EventName == EventNames.ON_EVENT_GROUP_ADMINSYSNOTIFY:
        return _GroupAdminsysnotifyEventMsg(ctx)
    return None


@_copy_ctx
def refine_group_shut_event_msg(ctx: EventMsg) -> _GroupShutEventMsg:
    """群禁言事件"""
    if not isinstance(ctx, EventMsg):
        raise InvalidContextError('Expected `EventMsg`, but got `%s`' % ctx.__class__)
    if ctx.EventName == EventNames.ON_EVENT_GROUP_SHUT:
        return _GroupShutEventMsg(ctx)
    return None


@_copy_ctx
def refine_group_admin_event_msg(ctx: EventMsg) -> _GroupAdminEventMsg:
    """管理员变更事件"""
    if not isinstance(ctx, EventMsg):
        raise InvalidContextError('Expected `EventMsg`, but got `%s`' % ctx.__class__)
    if ctx.EventName == EventNames.ON_EVENT_GROUP_ADMIN:
        return _GroupAdminEventMsg(ctx)
    return None
