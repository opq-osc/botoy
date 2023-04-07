from typing import Optional

from .models.group_msg import GroupMsg as _GroupMsg


class GroupMsg(_GroupMsg):
    @property
    def group_id(self) -> int:
        return self.MsgHead.GroupInfo.GroupCode  # type: ignore


class FriendMsg:
    pass


class EventMsg:
    pass


class Context:
    def __init__(self, data) -> None:
        self._data = data

    @property
    def group_msg(self) -> Optional[GroupMsg]:
        msg = None
        try:
            msg = GroupMsg.parse_raw(self._data)
        except Exception:
            pass
        ret = self.__dict__['group_msg'] = msg
        return ret

    @property
    def friend_msg(self) -> Optional[FriendMsg]:
        msg = None
        try:
            msg = FriendMsg.parse_raw(self._data)
        except Exception:
            pass
        ret = self.__dict__['friend_msg'] = msg
        return ret

    @property
    def event_msg(self) -> Optional[EventMsg]:
        msg = None
        try:
            msg = EventMsg.parse_raw(self._data)
        except Exception:
            pass
        ret = self.__dict__['event_msg'] = msg
        return ret
