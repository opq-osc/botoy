# 介绍

Botoy 是 OPQ 机器人框架的一个 Python 开发助手。对连接、消息解析、API 调用进行了封装，整体设计简单易用。

一个最简单的 Botoy 程序如下：

`bot.py`

```python
from botoy import bot, ctx, S

@bot
async def test():
    if ctx.g and ctx.g.text == 'test':
        await S.text('ok')

bot.print_receivers()
bot.run()
```

运行`python bot.py`, 输出结果如下：

```
+------+--------+-------+----------------+
| Name | Author | Usage |      Meta      |
+------+--------+-------+----------------+
| test |        |       | test.py line 4 |
+------+--------+-------+----------------+
ℹ️ 04-15 19:21:58 INFO 连接中[ws://localhost:8086/ws]...
✔️ 04-15 19:21:58 SUCCESS 连接成功!
```

以上程序便可实现在收到群消息为`test`时回复`ok`的功能。

当然，Botoy 也支持插件形式注册消息接收函数。
以下示例插件功能是在收到群消息或者好友消息的内容为`hello`时，回复`hello`的示例。

在`plugins`目录新建文件 `hello.py`。

```python
from botoy import ctx, S, mark_recv


async def hello():
    if msg := (ctx.g or ctx.f):
        if msg.text == 'hello':
            await S.text("Hello~")


mark_recv(hello)
```

修改`bot.py`

```diff
 from botoy import bot, ctx, S

 @bot
 async def test():
     if ctx.g and ctx.g.text == 'test':
         await S.text('ok')

+bot.load_plugins()
 bot.print_receivers()
 bot.run()
```

运行`bot.py`便能看到`hello`已被自动注册为接收函数。
