from botoy import decorators as deco


# 功能: 在收到群消息内容为 test 时, 在控制台打印 ok
# 如果是机器人本身的消息则忽略
########### 一般写法 ##########
@bot.on_group_msg
def group(ctx: GroupMsg):
    if ctx.FromUserId != ctx.CurrentQQ and ctx.Content == 'test':
        print('ok')


########### 使用装饰器 ##########
@bot.on_group_msg
@deco.ignore_botself
@deco.equal_content('test')
def group_(ctx: GroupMsg):
    print('ok')
