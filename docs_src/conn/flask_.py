from flask import Flask, request

from botoy import Botoy, EventMsg, FriendMsg, GroupMsg

app = Flask(__name__)
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


@app.route("/conn/<path>", methods=["POST"])
def conn(path: str):
    if path == "group":
        bot.group_msg_handler(request.json)
    elif path == "friend":
        bot.friend_msg_handler(request.json)
    elif path == "event":
        bot.event_handler(request.json)
    return "ok"


if __name__ == "__main__":
    app.run()
