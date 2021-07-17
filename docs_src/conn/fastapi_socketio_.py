from fastapi import FastAPI
from socketio import ASGIApp, AsyncServer

from botoy import Botoy, EventMsg, FriendMsg, GroupMsg

# --------------------------
bot = Botoy()


@bot.on_group_msg
def group(ctx: GroupMsg):
    print(
        f"收到群消息：群：{ctx.FromGroupName}({ctx.FromGroupId}) 发送人：{ctx.FromNickName}({ctx.FromUserId})"
    )


@bot.on_friend_msg
def friend(ctx: FriendMsg):
    print(f"收到好友 {ctx.FromUin} 的消息")


@bot.on_event
def event(ctx: EventMsg):
    print(f"收到事件：{ctx.EventName}")


# ----------------------------

sio = AsyncServer(async_mode="asgi")
sio.on("OnGroupMsgs", handler=bot.group_msg_handler)
sio.on("OnFriendMsgs", handler=bot.friend_msg_handler)
sio.on("OnEvents", handler=bot.event_handler)

# ----------------------------

app = FastAPI()
app.mount("/sio", ASGIApp(socketio_server=sio, socketio_path="socket.io"))
