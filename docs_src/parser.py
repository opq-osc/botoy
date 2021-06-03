from botoy import Botoy, GroupMsg
from botoy.parser import group as gp

bot = Botoy()


@bot.on_group_msg
def group(ctx: GroupMsg):
    # 打印图片消息每张图片的链接地址
    pic_data = gp.pic(ctx)
    if pic_data is not None:
        for pic in pic_data.GroupPic:
            print(pic.Url)
    # 如果机器人本艾特了，在控制台打印提示
    at_data = gp.at(ctx)
    if at_data is not None:
        if ctx.CurrentQQ in at_data.UserID:
            print(f"我是机器人，我现在被{ctx.FromNickName}艾特了，他说：{at_data.Content}")
