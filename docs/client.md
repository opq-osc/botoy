# 客户端

## 一个最简单的实例

```python
from botoy import Botoy, GroupMsg

bot = Botoy(12345678)

@bot.on_group_msg
def group(ctx: GroupMsg):
    print('收到群消息，群号为', ctx.FromGropId)

if __name__ == '__main__':
    bot.run()
```

这里假设你的 bot 端端口是 8888, 将上面这段代码拷贝到一个文件，运行后,
随便给机器人所在的群发一条消息，控制台应该会打印消息日志，并且会特别的显示代码中 print 出的内容

直接从库中导入类，传入 QQ 号实例一个 bot 对象，通过特定的装饰器，绑定该函数作为一个群消息接收函数，
接收函数有且仅接收一个参数 ctx, 同时还导入了一个 GroupMsg 类，这个是群消息上下文的类型，为了有代码提示，
使用类型注解语法，这样可以方便的知道有哪些支持的属性。正如上面的代码，ctx 的 FromGropId 属性就是该消息来自的群号

同样的，好友消息和事件消息分别对应 bot.on_friend_msg, FriendMsg 和 bot.on_event, EventMsg

**注意**:
你可以通过装饰器分别绑定任意多个接收函数，这样可以将不同的功能分隔开，而不是将逻辑全部挤在一个函数中

_Tips_:
装饰器也可以当做函数显式添加接收函数，该函数返回的是客户端实例本身，所以就有仓库 README.md 中的那行代码

## 配置实例

| 参数名             | 作用                                                                                                   | 默认值             |
| ------------------ | ------------------------------------------------------------------------------------------------------ | ------------------ |
| `qq`               | 如果不传则会监听服务端传过来的所有机器人的所有信息，如果传了，则会进行消息筛选, 仅接收对应机器人的信息 | `None`             |
| `use_plugins`      | 是否开启插件功能                                                                                       | `False`            |
| `port`             | bot 端运行端口                                                                                         | `8888`             |
| `host`             | bot 端 ip                                                                                              | `http://127.0.0.1` |
| `group_blacklist`  | 群黑名单, 此名单中的群聊消息不会被处理                                                                 | `[]`               |
| `friend_blacklist` | 好友黑名单 , 此名单中的好友消息不会被处理                                                              | `[]`               |
| `blocked_users`    | 屏蔽用户名单 ,忽略该名单内用户的消息                                                                   | `[]`               |
| `log`              | 是否开启日志                                                                                           | `True`             |
| `log_file`         | 是否输出日志文件                                                                                       | `True`             |

1. 参数均为可选值
2. 如果你想通过一个域名连接 bot 的话，将 port 设置为 0 即可
   如 bot 连接地址为 http://example.com, 设置`host='http://example.com'`, `port=0`

## 连接或断开连接时的钩子函数

- 使用`bot.when_connected`和`bot.when_disconnected`绑定 socketio 成功连接或断开连接时运行的函数，

- 有且只能绑定一个，函数不能有参数。

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

- `close` 停止运行
