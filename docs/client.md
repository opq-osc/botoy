# 客户端

## 一个最简单的实例

```python
from botoy import Botoy, GroupMsg

bot = Botoy(12345678)

@bot.on_group_msg
def group(ctx: GroupMsg):
    print('收到群消息，群号为', ctx.FromGroupId)

if __name__ == '__main__':
    bot.run()
```

这里假设你的 bot 端端口是 8888, 将上面这段代码拷贝到一个文件，运行后,
随便给机器人所在的群发一条消息，控制台应该会打印消息日志，并且会特别的显示代码中 print 出的内容

直接从库中导入类，传入 QQ 号实例一个 bot 对象，通过特定的装饰器，绑定该函数作为一个群消息接收函数，
接收函数有且仅接收一个参数 ctx, 同时还导入了一个 GroupMsg 类，这个是群消息上下文的类型，为了有代码提示，
使用类型注解语法，这样可以方便的知道有哪些支持的属性。正如上面的代码，ctx 的 FromGropId 属性就是该消息来自的群号

同样的，好友消息和事件消息分别对应 bot.on_friend_msg, FriendMsg 和 bot.on_event, EventMsg

### 通用接收函数

有的时候想在一个函数中处理多个类型的消息，只要将同一个函数装饰为多个类型的接收函数即可。

比如：

```python
def a(ctx):
  pass

bot.on_friend_msg(a).on_group_msg(a)
```

这样当接收到好友消息和群消息时，都会运行函数，参数为对应的消息

`bot.on`方法可以用来装饰通用的接收函数,
这个方法也算是一个语法糖，根据函数的参数签名来判断需要接收哪些消息

这里省略函数名

- 接收好友，群，事件三种消息，`ctx` 可能为 `FriendMsg`, `GroupMsg`, `EventMsg`
  1.  `(ctx)`
  2.  `(ctx: Union[FriendMsg, GroupMsg, EventMsg])`
- 接收单个消息, 以好友消息为例(`FriendMsg`)
  1. `(ctx: "FriendMsg")`
  2. `(ctx: FriendMsg)`
- 接收多个消息, 以好友消息(`FriendMsg`)和群消息为例(`GroupMsg`)
  1. `(ctx: Union[FriendMsg, GroupMsg])`

**注意**:
注册通用接收函数，**不可以使用任何一个接收装饰器**(接收函数装饰器在后面有说明),
因为这只是一个语法糖，可有可无而且需求很少，添加装饰器的支持，需要调整所有的装饰器，显得很没必要。

!!! tip

    1. 你可以通过装饰器分别绑定任意多个接收函数，这样可以将不同的功能分隔开，而不是将逻辑全部挤在一个函数中

    2. 装饰器也可以当做函数显式添加接收函数，该函数返回的是客户端实例本身，所以就有仓库 README.md 中的那行代码

## 配置实例

| 参数名             | 作用                                                                                                                                   | 默认值             |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| `qq`               | 如果不传则会监听服务端传过来的所有机器人的所有信息，如果传了，则会进行消息筛选, 仅接收对应机器人的信息。QQ 号为 0 会被忽略，相当于没传 | `None`             |
| `use_plugins`      | 是否开启插件功能                                                                                                                       | `False`            |
| `port`             | bot 端运行端口                                                                                                                         | `8888`             |
| `host`             | bot 端 ip                                                                                                                              | `http://127.0.0.1` |
| `group_blacklist`  | 群黑名单, 此名单中的群聊消息不会被处理                                                                                                 | `[]`               |
| `friend_blacklist` | 好友黑名单 , 此名单中的好友消息不会被处理                                                                                              | `[]`               |
| `blocked_users`    | 屏蔽用户名单 ,忽略该名单内用户的消息                                                                                                   | `[]`               |
| `log`              | 该参数控制控制台日志等级,为 True 输出 INFO 等级日志,为 False 输出 EROOR 等级的日志                                                     | `True`             |
| `log_file`         | 该参数控制日志文件开与关,为 True 输出 INFO 等级日志的文件,为 False 关闭输出日志文件                                                    | `False`            |

1. 参数均为可选值
2. **如果你想通过一个域名连接 bot 的话，将 port 设置为 0 或 80 即可
   如 bot 连接地址为 http://example.com, 设置`host='http://example.com'`, `port=0`**
3. 关于日志，环境变量`BOTOY_LOG_LEVEL`拥有最高优先级，如果设置了该环境变量，所有 log handler 的等级都以此为准.
4. socketio 日志默认为`INFO`， 有需要的话通过这样修改

   ```python
   import logging

   logging.getLogger('socketio.client').setLevel(logging.ERROR)
   ```

## 连接或断开连接时的钩子函数

- 使用`bot.when_connected`和`bot.when_disconnected`绑定 socketio 成功连接或断开连接时运行的函数(可选)

- 只能绑定**一个**，函数不能有参数。

- 因为 socketio 有自动重连，默认情况下两个函数都只会运行一次，如果需要每次都要运行的话，可以设置装饰器参数`every_time`来决定每次连接或断开连接后是否都运行

```python

@bot.when_connected
def _():
    print('连接成功啦~, 我只提醒你一次')

@bot.when_connected(every_time=True)
def _():
    print('连接成功啦~, 每次连接成功我都会提醒你')
```

## 实例方法

- `run` 启动
- `run_no_wait` 启动，但不会阻塞

## 消息上下文对象

对三类消息及其字段的简要说明

### 群消息(GroupMsg)

| 字段名        | 说明                              |
| ------------- | --------------------------------- |
| CurrentQQ     | 当前机器人 qq                     |
| FromGroupId   | 群号                              |
| FromGroupName | 群名称                            |
| FromUserId    | 发送人 QQ                         |
| FromNickName  | 发送人昵称                        |
| Content       | 发送内容                          |
| MsgType       | 消息类型                          |
| MsgTime       | 消息发送时间                      |
| MsgSeq        | ~                                 |
| MsgRandom     | ~                                 |
| RedBaginfo    | 红包信息相关                      |
| message       | 由 websocket 传过来的原始字典数据 |
| data          | 原始数据中的 Data 字段            |

### 好友消息(FriendMsg)

| 字段名     | 说明                                                                                         |
| ---------- | -------------------------------------------------------------------------------------------- |
| CurrentQQ  | 当前机器人 qq                                                                                |
| FromUin    | 发送人 qq                                                                                    |
| TempUin    | 如果不为 None，表示为私聊消息，该字段是发起私聊的入口群号。同时 MsggType 就是 TempSessionMsg |
| ToUin      | 发给谁的，一般就是机器人啦                                                                   |
| MsgType    | 消息类型                                                                                     |
| MsgTime    | 消息发送时间                                                                                 |
| MsgSeq     | ~                                                                                            |
| Content    | 发送内容                                                                                     |
| RedBaginfo | 红包信息相关                                                                                 |
| message    | 由 websocket 传过来的原始字典数据                                                            |
| data       | 原始数据中的 Data 字段                                                                       |

### 事件(EventMsg)

| 字段名     | 说明                              |
| ---------- | --------------------------------- |
| CurrentQQ  | 当前机器人 qq                     |
| EventName  | 事件名称                          |
| EventData  | 事件的具体信息(每个事件都不同)    |
| EventMsg   | 事件的基本信息(每个事件都有)      |
| Content    | 事件的内容                        |
| FromUin    | 可能是群号、好友 qq               |
| ToUin      | ~                                 |
| MsgSeq     | ~                                 |
| RedBaginfo | ~                                 |
| message    | 由 websocket 传过来的原始字典数据 |
| data       | 原始数据中的 Data 字段            |

!!! tip

    - 群消息和好友消息中的Content字段永远是字符串类型，如果是非文本消息，就是json格式字符串数据，需要另外解码
    - 对字段有疑问请自行打印出来或查看源码对比原数据，字段的命名也是与原数据中命名一致
