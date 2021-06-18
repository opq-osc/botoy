from flask import Flask
from flask_socketio import SocketIO

from botoy import Botoy, EventMsg, FriendMsg, GroupMsg

app = Flask(__name__)
sio = SocketIO(app)
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


sio.on("OnGroupMsgs")(bot.group_msg_handler)
sio.on("OnFriendMsgs")(bot.friend_msg_handler)
sio.on("OnEvents")(bot.event_handler)


if __name__ == "__main__":
    sio.run(app)
