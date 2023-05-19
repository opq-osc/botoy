# 消息上下文 `ctx`

```python
from botoy import ctx
```

消息上下文只能在接收函数中使用，其包含当前消息的所有内容。

- `ctx.data`为当前消息的原始数据。
- `ctx.group_msg`(alias: `ctx.g`)为群消息(`GroupMsg`)，非群消息时为`None`
- `ctx.friend_msg`(alias: `ctx.f`)为好友消息(`FriendMsg`)，非好友消息时为`None` (包括私聊)
- `ctx.event_msg`(alias: `ctx.e`)为事件消息(`EventMsg`)，非事件消息时为`None`

目前事件消息还不可用。

# 上下文可使用总览

抽象类BaseMsg：这是一个抽象基类，定义了处理消息的基本方法和属性。具体的子类需要实现model属性，并可以使用c函数缓存一些属性值。

类GroupMsg：继承自BaseMsg，表示群组消息。该类接受一个字符串或字典作为输入参数，并根据参数创建对应的数据模型对象。该类重写了model属性和一些其他属性，用于获取消息的具体信息。

类FriendMsg：继承自BaseMsg，表示好友消息。与GroupMsg类似，该类接受一个字符串或字典作为输入参数，并根据参数创建对应的数据模型对象。该类也重写了model属性和一些其他属性，用于获取消息的具体信息。

类EventMsg：表示事件消息。目前该类的实现未完成，抛出了NotImplementedError。

类Context：表示消息上下文。该类接受一个字符串作为输入参数，并将其解析为JSON格式的数据。通过属性访问的方式，可以获取当前机器人QQ号、群组消息、好友消息和事件消息。

其他辅助函数和变量：代码中还包含了一些辅助函数和变量，用于辅助处理消息上下文。

# 类BaseMsg
该类为最基础的解析群消息格式，其他的类（如GroupMsg,FriendMsg,EventMsg）都可通过该类获得消息


## 最简程序
```python
from botoy import ctx
async def hellworld():
    if g := ctx.g: ## ctx.g = ctx.groupMsg 也可更换为ctx.f/ctx.e 分别为群消息，好友消息，事件消息
        if g.text == 'hellowolrd'
        print('你好')
```
## 细则
msg_head是一个属性，返回CurrentPacket.EventData.MsgHead，数据类型为对象。

msg_body是一个属性，返回CurrentPacket.EventData.MsgBody，数据类型为对象。

images是一个属性，返回图片列表，可能为None，数据类型为列表 (List)，其中列表中的元素是图片对象。

voice是一个属性，返回语音，可能为None，数据类型为语音对象。

video是一个属性，返回短视频，可能为None，数据类型为短视频对象。

text是一个属性，返回文字内容，数据类型为字符串 (str)。

is_from_self是一个属性，判断消息是否来自机器人自身，返回布尔值 (bool)。

sender_uin是一个属性，返回发送者的QQ号，数据类型为整数 (int)。

sender_nick是一个属性，返回发送者的昵称，数据类型为字符串 (str)。

from_type是一个属性，返回CurrentPacket.EventData.MsgHead.FromType，数据类型为整数 (int)。

bot_qq是一个属性，返回接受到消息机器人的QQ号，数据类型为整数 (int)。

这些属性提供了消息头和消息体的相关信息，例如消息的随机数、序列号、时间戳、UID、消息类型、发送者的QQ号和昵称，以及机器人的QQ号。返回的数据类型根据属性的定义而定，可以是对象、整数、字符串或列表。

# 类GroupMsg
该类主要是通过获取群消息，来解析上下文
## 最简程序
```python
from botoy import ctx
async def hellworld():
    if g := ctx.g:
        if g.text == 'hellowolrd'
        print('你好')
```
## 细则
from_group是一个属性，返回群组的ID，数据类型为整数 (int)。通过访问msg_head的FromUin属性来获取。

from_group_name是一个属性，返回群组的名称，数据类型为字符串 (str)。通过访问msg_head的GroupInfo属性中的GroupName属性来获取。

from_user是一个属性，返回消息的发送者的QQ号，数据类型为整数 (int)。通过访问msg_head的SenderUin属性来获取。

from_user_name是一个属性，返回消息的发送者的昵称，数据类型为字符串 (str)。通过访问msg_head的SenderNick属性来获取。

at_list是一个属性，返回被艾特的用户列表，数据类型为列表 (List)，其中列表中的元素是包含用户信息的对象。通过访问msg_body的AtUinLists属性来获取，如果属性不存在，则返回空列表。

is_at_user是一个方法，用于判断是否艾特了某个用户。它接受一个整数类型的用户ID作为参数，返回值为布尔值 (bool)。它接受一个整数类型的用户ID作为参数，然后检查该用户ID是否在被艾特列表中。

is_at_bot是一个属性，返回是否艾特了机器人，数据类型为布尔值 (bool)。它通过调用is_at_user方法，并传入机器人的QQ号（model.CurrentQQ）作为参数来判断是否艾特了机器人。

revoke是一个异步方法，用于撤回该消息。它使用action.Action对象创建了一个异步上下文管理器，并调用其revoke方法来实现消息的撤回操作。

这些属性和方法提供了方便的方式来获取群组消息的相关信息，并进行相应的操作，比如判断是否艾特了某人、判断是否艾特了机器人，以及撤回消息等。

# 类FriendMsg
该类主要是通过获取好友与私聊消息，解析上下文
## 最简程序
```python
from botoy import ctx
async def hellworld():
    if g := ctx.f:
        if g.text == 'hellowolrd'
        print('你好')
```
## 细则
from_user是一个属性，返回发送者的QQ号，数据类型为整数 (int)。
from_user_name是一个属性，返回发送者的昵称，数据类型为字符串 (str)。
is_private是一个属性，判断消息是否为私聊，返回布尔值 (bool)。如果调用from_group属性时产生异常，则消息为私聊，返回True；否则，返回False。
from_group是一个属性，返回发送者的群号。仅在私聊时才有值，否则会引发异常。数据类型为整数 (int)。
is_from_phone是一个属性，判断消息是否来自手机。如果消息体为空，且发送者的QQ号与接收者的QQ号相同，并且消息类型为529，则表示消息来自手机，返回布尔值 (bool)。
这些属性和方法提供了关于发送者的一些信息，例如发送者的QQ号、昵称以及私聊和手机端的相关判断。返回的数据类型为整数、字符串或布尔值。

