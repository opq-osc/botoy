import traceback
from typing import AnyStr, List, Optional

from pydantic import BaseModel

from .models import group_msg as g


def c(obj, key, value):  # c => cache
    obj.__dict__[key] = value
    return value


class GroupMsg(g.GroupMsg):
    @property
    def from_group(self) -> int:
        # TODO: GroupInfo 有时候没有，需要确认
        return c(self, 'from_group', self.CurrentPacket.EventData.MsgHead.GroupInfo.GroupCode)  # type: ignore

    @property
    def images(self):
        return c(self, 'images', self.CurrentPacket.EventData.MsgBody.Images)

    @property
    def voice(self):
        return c(self, 'voice', self.CurrentPacket.EventData.MsgBody.Voice)

    @property
    def video(self):
        return c(self, 'video', self.CurrentPacket.EventData.MsgBody.Video)

    @property
    def at_list(self):
        return c(self, 'at_list', self.CurrentPacket.EventData.MsgBody.AtUinLists or [])

    @property
    def text(self):
        return c(self, 'text', self.CurrentPacket.EventData.MsgBody.Content)

    def is_at_user(self, user_id: int):
        return user_id in (i.QQUid for i in self.at_list or [])

    @property
    def is_at_bot(self):
        return c(self, 'is_at_bot', self.is_at_user(self.CurrentQQ))

    @property
    def is_from_self(self):
        return c(
            self,
            'is_from_self',
            self.CurrentQQ == self.CurrentPacket.EventData.MsgHead.SenderUin,
        )

    @property
    def sender_uin(self):
        return c(self, 'sender_uin', self.CurrentPacket.EventData.MsgHead.SenderUin)

    @property
    def sender_nick(self):
        return c(self, 'sender_nick', self.CurrentPacket.EventData.MsgHead.SenderNick)


class FriendMsg(BaseModel):
    pass


class EventMsg(BaseModel):
    pass


class Context:
    def __init__(self, data: AnyStr) -> None:
        self._data = data

    @property
    def group_msg(self) -> Optional[GroupMsg]:
        msg = None
        try:
            msg = GroupMsg.parse_raw(self._data)
        except Exception:
            print(traceback.format_exc())

        return c(self, 'group_msg', msg)

    @property
    def friend_msg(self) -> Optional[FriendMsg]:
        msg = None
        try:
            msg = FriendMsg.parse_raw(self._data)
        except Exception:
            pass
        return c(self, 'friend_msg', msg)

    @property
    def event_msg(self) -> Optional[EventMsg]:
        msg = None
        try:
            msg = EventMsg.parse_raw(self._data)
        except Exception:
            pass
        return c(self, 'event_msg', msg)
