# 会话 (start_session)

```python
from botoy import start_session
```

**当前只支持异步`receiver`中使用**

在 receiver 中根据你的需求，使用`start_session`函数开启会话，该函数返回所开启的会话对象。

以下为函数签名:

```python
def start_session(
    group: Optional[Union[bool, int]] = None,
    friend: Optional[Union[bool, int]] = None,
    multi_user: Optional[bool] = None,
    skip_responder: bool = True,
) -> "SessionExport":
    """开启会话

    约定：只分群消息和好友消息，好友消息与私聊消息在本节所表示含义一致。

    Args: group friend multi_user

    >>> 参数group和friend都不是整数类型的情况 <<<

    由群消息开启会话
    ================

    -

    A. ``group=True``, ``friend``参数失效

    - ``multi_user=True``
        会话为该群所有用户共享。该群所有消息都会被捕获。``session``无法获取下一条好友消息（无法调用``f``方法，并且``ctx``方法只返回群消息）

    - ``multi_user=False``
        会话为该群该用户共享，同时自动支持好友消息。来自该用户在该群的消息以及该用户的私聊消息都会被捕获。

    B. ``friend=True``

    开启与该用户的私聊会话。只捕获该用户的私聊消息。

    C. 默认行为

    会话为该群该用户共享，同时自动支持好友消息。来自该用户在该群的消息以及该用户的私聊消息都会被捕获。


    由私聊消息开启会话
    ==================

    固定一种行为（参数全部无效）。开启与该用户的私聊会话。只捕获该用户的私聊消息。


    由事件消息开启会话
    ==================

    暂不支持

    参数处理或组合的优先级为：group > multi_user > friend
    -

    >>> 参数group和friend存在整数类型的情况 <<<

    直接传入群ID，用户ID来开启指定对话

    - 仅指定群id(group)时：参数friend和multi_user均被忽略。此时捕获指定群所有消息。

    - 仅指定用户id(friend)时：参数group和multi_user均被忽略。此时仅捕获指定用户私聊消息。

    - 同时指定群id(group)和用户id(friend)时：

      如果开启多用户(multi_user)，将忽略参数friend。此时捕获指定群所有消息。
      如果关闭多用户(multi_user)，此时捕获该群来自该用户在该群的消息以及该用户的私聊消息。

    参数处理或组合的优先级为：group > multi_user > friend
    -

    Args: skip_responder
    -

    参数``skip_responder``表示跳过抢答。在处在对话中，程序还在处理其他逻辑，此时并不需要用户的输入，但用户仍然可能发送信息，比如用户对当前功能十分熟悉。
    该行为被定义为抢答。
    当该参数为``True``时，仅当``正在``请求用户消息时才会处理新消息。
    当该参数为``False``时，用户消息会被存入队列，当请求用户消息时，会直接作为最新消息返回。
    """
```

## 会话可用属性和方法

- `set_default_timeout`: 设置各个方法的默认超时时间
- `finish`: 直接结束对话，该方法通过抛出特定错误来结束后续所有对话。所以你的代码中始终不应该出现`except:` 或`except Exception` 这种捕获所有错误的语句。
- `set_finish_info`: 设置`finish` 方法的默认提示信息。默认为空即不发送任何提示。

| 方法         | 说明                                         |
| ------------ | -------------------------------------------- |
| `text`       | 获取下一条文本信息                           |
| `must_text`  | 和`text`类似，但获取超时会直接结束对话       |
| `image`      | 获取下一条图片信息, 需要注意返回的是图片列表 |
| `must_image` | 和`image`类似，但获取超时会直接结束对话      |
| `g`          | 获取下一条群消息(GroupMsg)                   |
| `must_g`     | 和`g`类似，但获取超时会直接结束对话          |
| `f`          | 获取下一条好友或私聊消息(FriendMsg)          |
| `must_f`     | 和`f`类似，但获取超时会直接结束对话          |
| `ctx`        | 获取下一条消息上下文                         |
| `must_ctx`   | 和`ctx`类似，但获取超时会直接结束对话        |
| `confirm`    | 提示用户确认消息。用于询问是否执行某操作     |
| `select`     | 提示用户从列表中选择一项。                   |

`confirm`和`select`是基于`text`进行封装的，你如果不喜欢框架提供的交互形式，可以仿照进行封装。

## 示例

### 鹦鹉学舌

需求：

1. 当群消息为`start`时开启对话
2. 不断重复用户所发信息
3. 当用户信息为`q`时停止对话
4. 20s 用户未发送信息便结束对话
5. 结束对话需发送提示信息如：对话已结束

实现：

```python
from botoy import ctx, start_session, S

async def r_repeat():
    if ctx.g and ctx.g.text == 'start':
        FINISH_INFO = '对话已结束'
        ss = start_session(
            group=True, multi_user=False
        )  # 开启与该用户的会话，接收该用户在此群消息以及私聊(好友)消息
        ss.set_default_timeout(20)  # 设置20s超时，默认为30s
        ss.set_finish_info(FINISH_INFO)  # 后面会告诉你有啥用
        await S.text('鹦鹉学舌')  # 提示用户
        while True:
            text, s = await ss.text()  # 等待用户信息。返回元组，分别是消息以及绑定了新消息的S
            if text is None:  # 超时
                ss.finish(FINISH_INFO)  # 结束对话，后面代码将不再被执行, 此处提供了提示信息
            if text == 'q':  # 输入 q
                ss.finish()  # 此处没提供提示信息，但是由于此前设置了默认提示信息，所以此处仍会发送提示
            if not text:
                continue  # 为空就忽略
            await s.text(text)
```

![repeat](https://github.com/opq-osc/botoy/assets/47070852/82e7bd51-b7b9-4d69-95d1-9e522eecec13)

### 信息录入 v1

需求：

1. 用户可在群聊或私聊中发送`login`开启会话
2. 但只支持私聊中进行后续操作
3. 依次询问用户提供账号、密码
4. 获取完成后，回复用户账号，密码

实现：

```python
from botoy import ctx, start_session

async def login():
    if msg := (ctx.g or ctx.f):  # 群和私聊都可以
        if msg.text == 'login':
            ss = start_session(friend=True)  # 只开启私聊会话
            ss.set_finish_info("输入超时，对话结束")
            username, s = await ss.must_text("请输入用户名")  # 该方法超时会直接结束对话
            password, s = await ss.must_text("请输入密码")
            await s.text(f"您的用户名为：{username}\n您的密码为：{password}")
```

![login](https://github.com/opq-osc/botoy/assets/47070852/782e5dbd-af44-4570-82aa-2358b9f494b2)

### 信息录入 v2

需求：

在 v1 的基础上，增加确认提示。如果用户确认，则提示“登录成功”。如果用户未确认，则提示用户重新开启会话。

实现：

```python
from botoy import ctx, start_session

async def r_login():
    if msg := (ctx.g or ctx.f):
        if msg.text == 'login':
            ss = start_session(friend=True)
            ss.set_finish_info("输入超时，对话结束")
            username, s = await ss.must_text("请输入用户名")
            password, s = await ss.must_text("请输入密码")
            info = f"您的用户名为：{username}\n您的密码为：{password}\n请确认是否输入无误。"
            if await ss.confirm(info):
                await s.text("登录成功")
            else:
                await s.text("确认超时或确认失败，请重新登录！")
```

![yes](https://github.com/opq-osc/botoy/assets/47070852/b5176839-23d9-4fc9-9af1-9bcca7fd5022)

...
