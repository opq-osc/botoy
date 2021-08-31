# 使用异步

```python
import asyncio

from botoy import AsyncBotoy, GroupMsg, S, AsyncAction
from botoy.async_decorators import ignore_botself

bot = AsyncBotoy()


@bot.on_group_msg
@ignore_botself
async def test_action(ctx: GroupMsg):
    if ctx.Content == "test":
        async with AsyncAction(ctx.CurrentQQ) as action:
            await action.sendGroupText(ctx.FromGroupId, 'test ok => action')
        await asyncio.sleep(1)
        await S.bind(ctx).atext('test ok => S')


if __name__ == "__main__":
    asyncio.run(bot.run())
```

<sub><code>发送 'test' 回复 'test ok'</code></sub>

## 客户端`AsyncBotoy`

中间件，连接和断开连接的钩子函数仍然要求是同步

其他不变，`run`方法是异步

## 动作 `AsyncAction`

多了一个关闭操作

使用 with 语法

```python
async with AsyncAction() as action:
    ...
```

或显式关闭

```python
action = AsyncAction()
...
await action.close()
```

## 接收函数装饰器`async_decorators`

适用于异步接收函数的装饰器, 用法一致

```python
from botoy.async_decorators import ignore_botself

@ignore_botself
async def receive_group_msg(ctx):
  ...
```

## 语法糖 `S`

```
await S.atext()
await S.aimage()
await S.avoice()

await S.bind(ctx).atext()
await S.bind(ctx).aimage()
await S.bind(ctx).avoice()

```

## 注意

- 接收函数可以是同步或异步
- session 只支持同步
