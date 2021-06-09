from typing import Any, Callable, Optional

from .model import EventMsg, FriendMsg, GroupMsg

"""群消息接收函数"""
T_GroupMsgReceiver = Callable[[GroupMsg], Any]

"""好友消息接收函数"""
T_FriendMsgReceiver = Callable[[FriendMsg], Any]

"""事件接收函数"""
T_EventReceiver = Callable[[EventMsg], Any]

"""群消息中间件"""
T_GroupMsgMiddleware = Callable[[GroupMsg], Optional[GroupMsg]]

"""好友消息中间件"""
T_FriendMsgMiddleware = Callable[[FriendMsg], Optional[FriendMsg]]

"""事件中间件"""
T_EventMiddleware = Callable[[EventMsg], Optional[EventMsg]]
