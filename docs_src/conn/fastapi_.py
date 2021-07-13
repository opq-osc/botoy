from fastapi import FastAPI, Request

from botoy import Botoy, EventMsg, FriendMsg, GroupMsg

app = FastAPI()
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


@app.post("conn/{path}")
async def conn(path: str, request: Request):
    if path == "group":
        bot.group_msg_handler(await request.json())
    elif path == "friend":
        bot.friend_msg_handler(await request.json())
    elif path == "event":
        bot.event_handler(await request.json())
    return "ok"


if __name__ == "__main__":
    print(
        """
    pip install uvicorn
    uvicorn fastapi_:app
    """
    )
