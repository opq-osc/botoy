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
| 属性             | 说明                             | 返回类型          |
|------------------|--------------------------------|-------------------|
| msg_head         | 当前消息的头部信息               | 对象              |
| msg_body         | 当前消息的内容信息               | 对象              |
| images           | 图片列表，可能为None             | 列表 (List)       |
| voice            | 语音，可能为None                 | 语音对象          |
| video            | 短视频，可能为None               | 短视频对象        |
| text             | 文字内容                         | 字符串 (str)      |
| is_from_self     | 判断消息是否来自机器人自身       | 布尔值 (bool)     |
| sender_uin       | 发送者的QQ号                     | 整数 (int)        |
| sender_nick      | 发送者的昵称                     | 字符串 (str)      |
| from_type        | 消息来源的类型                   | 整数 (int)        |
| bot_qq           | 接收到消息机器人的QQ号            | 整数 (int)        |

这些属性提供了关于消息的头部信息和内容信息的相关数据，例如消息的发送者信息（QQ号、昵称）、消息类型、消息的文本内容，以及消息是否来自机器人自身。返回的数据类型根据属性的定义而定，可以是对象、整数、字符串或列表。

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
| 属性              | 说明                             | 返回类型         |
|-------------------|--------------------------------|------------------|
| from_group        | 群组的ID                         | 整数 (int)       |
| from_group_name   | 群组的名称                       | 字符串 (str)     |
| from_user         | 消息的发送者的QQ号               | 整数 (int)       |
| from_user_name    | 消息的发送者的昵称               | 字符串 (str)     |
| at_list           | 被艾特的用户列表                 | 列表 (List)      |
| is_at_user        | 判断是否艾特了某个用户           | 布尔值 (bool)    |
| is_at_bot         | 是否艾特了机器人                 | 布尔值 (bool)    |
| revoke            | 异步方法，用于撤回该消息         | 无返回值         |

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
| 属性            | 说明                                                   | 返回类型       |
|-----------------|------------------------------------------------------|--------------|
| from_user       | 发送者的QQ号                                           | 整数 (int)     |
| from_user_name  | 发送者的昵称                                           | 字符串 (str)   |
| is_private      | 判断消息是否为私聊                                     | 布尔值 (bool)  |
| from_group      | 发送者的群号                                           | 整数 (int)     |
| is_from_phone   | 判断消息是否来自手机                                   | 布尔值 (bool)  |