from botoy import Action, Botoy, GroupMsg
from botoy.collection import MsgTypes
from botoy.decorators import ignore_botself, these_msgtypes
from botoy.session import SessionController
from botoy.sugar import Text

host = None
qq = None
assert all([host, qq])
bot = Botoy(qq=qq, host=host, log=False)
action = Action(qq, host=host)


# 功能1, 查询
# 指令查询+关键字
def search(word):
    return f'已查询{word}'


# 新建一个会话控制器，每个功能对应一个控制器(我是避免用这样听起来很高级的名词的,但这里我也不知道用什么描述比较好)
# 这里的参数表示生成的session无任何操作该时长后被自动关闭
sc = SessionController(1 * 60)


@bot.on_group_msg
@ignore_botself
@these_msgtypes(MsgTypes.TextMsg)
def _(ctx: GroupMsg):
    if ctx.Content.startswith('查询'):
        # 取需要查询的内容，如果发送的消息直接包含了需要查询的关键字
        # 则直接返回查询结果即可
        word = ctx.Content[2:].strip()
        if word:
            Text(search(word))
        # 如果只触发了查询指令但未直接提供关键字，则需要提示用户发送关键字
        else:
            with sc.get_session(ctx) as session:  # 请务必使用with语句
                Text('查询那个城市的天气呢？15秒内回复')  # 提示用户发送天气
                # 获取session中的word字段，该方法会一直阻塞，直到需要获取的数据被设置
                # 该方法接收三个参数，第一个参数为需要接收的数据名(键),
                # 第二个参数为允许等待的时长，超过该时长, 方法不再阻塞，返回默认值
                # 第三个参数即为上句话提到的超时返回默认值, 默认为None
                word = session.get('word', 15)  # 这里即为获取word字段，允许等待15秒
                if word is not None:  # 这里说明正确的取到了word值, 发送结果
                    Text(search(word))
                else:  # 这里说明等待超时，即用户没有及时回复
                    Text('我等得太累了，需要查询，请再次发送”查询“指令')
                # 当执行到最后一步，如果没有其他获取操作，说明该次会话已经结束，session会自动设置成关闭状态
    else:  # 上面需要获取数据，那这一步可想而知是设置数据
        with sc.get_session(ctx) as session:  # 只要session不是关闭状态，获取到的session对象是唯一且相同的，
            # 如果该session和上面的session一样，说明session不是初次启动，那么此时用户所发送的消息
            # 应该用来设置所需要的数据,
            # 所以如何判断该session是否在等待数据被设置？
            if session.waiting:  # 只要session被get操作阻塞时，该属性就为True
                # 所以我们将此次所接收到的消息设置为所需要的word数据
                session.set('word', ctx.Content)
            # 如果此次收到的消息的发送者不是触发指令的用户，那么这里的session是新建的，也是不需要的。
            # 此时退出with语句时会被自动关闭，事实上就算没有被关闭也没事，因为这里的无用session没有被需要获取数据，
            # waiting属性一直是False，然而所有的操作流程中，都需要判断waiting属性


# 功能2 生成名片
# 用户发送‘生成名片’后，机器人一次询问姓名，性别，国籍，最后整理在一起并汇报
sc2 = SessionController()  # 新建一个会话控制器，每个功能对应一个控制器


@bot.on_group_msg
@ignore_botself
@these_msgtypes(MsgTypes.TextMsg)
def _(ctx: GroupMsg):
    if ctx.Content == '生成名片':  # 触发指令
        with sc2.get_session(ctx) as session:
            # 这里在功能1的基础上补充对上面获取session方法的说明
            # 如果用户下面的步骤执行到性别部分时，又发送生成名片指令进入到这一步
            # session未关闭的情况下，下面的提示操作会再次发送，
            # 但因为session中name字段已存在，那么name会立即获取到。
            # 此时会出现套娃。所以需要进行更多的判断

            # 这里的说明看不懂没关系，我已经解释不下去了,
            # 因为我也搞不懂所有存在的情况和逻辑，能力有限，目前只能封装到这一步
            # 如果你有好的想法和改进，欢迎交流和pr
            Text('你的名字？')
            name = session.get('name')
            Text('你的性别?')
            gender = session.get('gender')
            Text('你的国籍?')
            country = session.get('country')
            Text(f'你叫{name}, 性别是{gender}, 来自{country}')
    with sc2.get_session(ctx) as session:
        if session.waiting:
            # 因为这次需要设置多个数据，这里用到新的方法 session.has
            if not session.has('name'):  # 如果session中没有 name
                session.set('name', ctx.Content)  # 那么这次的消息就是设置name参数
            elif not session.has('gender'):  # 同理
                session.set('gender', ctx.Content)
            elif not session.has('country'):  # 同理
                session.set('country', ctx.Content)


if __name__ == "__main__":
    bot.run()
