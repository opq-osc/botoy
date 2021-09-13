# 连续对话

# 目前仍是雏形，后续可能对功能进行重构导致大量 breaking changes

该模块主要封装了几个数据结构，提供各种操作方法，通过这些方法来将逻辑组合起来

下面只介绍真正要用的类型

## Session

类似字典类型, 作用中提到的数据指键值对数据中的键

| 方法        | 作用                                                                                           |
| ----------- | ---------------------------------------------------------------------------------------------- |
| get         | 获取数据                                                                                       |
| pop         | 获取数据,返回后马上移除                                                                        |
| set         | 设置数据                                                                                       |
| has         | 查看数据是否存在                                                                               |
| clear       | 清除所有数据                                                                                   |
| remove      | 清除指定的数据                                                                                 |
| waiting     | 判断是否正在等待数据被设置                                                                     |
| wait_for    | 主动添加需要被设置的数据                                                                       |
| do_not_wait | 主动删除需要被设置的数据                                                                       |
| close       | 关闭该 session                                                                                 |
| want        | 与 get 相似，但支持设置参数来快速对 session 进行回复 , 如果设置参数 pop 为 True，则与 pop 类似 |
| send_text   | 对该 session 发送文字                                                                          |
| send_pic    | 对该 session 发送图片                                                                          |
| choose      | 提示用户发送序号选择列表中的一项                                                               |

| 属性     | 作用                                        |
| -------- | ------------------------------------------- |
| empty    | 是否为空                                    |
| waitings | 正在等待被设置的数据                        |
| action   | 与该 session 对应的预先初始化的 Action 对象 |

## SessionHandler

每个插件对应一个 SessionHandler，需要自行定义

### 初始化参数说明

#### filters

session 开启的条件，接收若干个筛选函数，函数的参数为消息上下文 ctx,
函数返回`botoy.session.FILTER_SUCCESS`表示筛选通过。函数可自行编写也可以直接使用接收函数装饰器

示例

```python
from botoy.session import FILTER_SUCCESS, SessionHandler
from botoy.decorators import ignore_botself, equal_content

def my_filter(ctx):
  if ctx.FromUserId != 10:
    return FILTER_SUCCESS
example_handler = SessionHandler(ignore_botself, equal_content('session'), my_filter)
```

以上表示 session 开启的条件为：非机器人自身消息，发送内容为 session, 用户 ID 不是 10

#### single_user

会话分三种类型，群所有用户、群单个用户、好友
若该参数为`True`，表示仅对单个用户有效

#### expiration

session 如果**无任何操作**超过该时长，将自动关闭

### 方法说明

#### receive_group_msg、receive_friend_msg

插件需要接收消息，需要提供函数`receive_group_msg`(群消息)和`receive_friend_msg`(好友消息)

可以这样接收消息

```python
example_handler = SessionHandler()

def receive_group_msg(ctx): # 注册群消息
  example_handler.message_receiver(ctx)

def receive_friend_msg(ctx): # 注册好友消息
  example_handler.message_receiver(ctx)
```

也可以这样接收消息

```python
example_handler = SessionHandler()
example_handler.receive_group_msg() # 注册群消息
example_handler.receive_friend_msg() # 注册好友消息

# 但推荐这样
example_handler = SessionHandler().receive_group_msg().receive_friend_msg()
```

按需要选择需要接收的消息，如果选择多个，后续对 ctx 进行操作时，要进行必要的判断

#### 装饰器 handle

该装饰器注册一个函数(`handler`)。函数无参数。

在 session 被新建后运行, 并且在 session 存在期间只会运行一次

这是最主要的函数，在该函数内对 session 进行操作。需要注意的是，该函数内的 ctx 一直是触发 session 创建的 ctx

#### 装饰器 receive

该装饰器注册一个函数(`receiver`)。函数无参数。

session 开启后，**每次接收到新消息都会运行该函数**，该函数也可对 session 进行操作，同时 ctx 是对应新消息的

#### 装饰器 parse

该装饰器注册一个函数(`parser`)。函数接收一个参数 ctx

session 开启后，每次接收到新消息，都会判断该 session 正在等待的数据，
如果有数据正在等待被设置，则调用 parser，并将其返回值作为该数据设置为等待列表的第一个,
默认将 ctx.Content 作为数据。

等待数据是什么意思？

0. 由 session 的`get`、`pop`方法指定的键名，如果设置了参数`wait=True`, 则改键开始等待，直到超时或数据被设置
1. 使用`want`方法，该方法是 get 方法的封装，加了一个快速回复 session 的功能
2. 使用`wait_for`方法显式指定一个键名

#### 装饰器 got

该装饰器注册一个或多个函数(`condition_handler`)

got 中设置若干个 key，当 session 中同时存在所有的 key 时，该函数将被调用(这里的调用并不是立即调用, 每次接收到新消息判断一次, 由于这点，所以需要配合 receiver 或 handler 的进行使用才行, 具体逻辑看自己需要)
正常情况下，该函数只会被调用一次。

例

```python
@example_handler.got('name')
def _():
  name = session.get('name')
  print(f'Hello {name}!')

@example_handler.got('age')
def _():
  age = session.get('age')
  print(f'You are {age} years old.')
```

注册的函数参数是可选的，可以将 got 中指定的 keys 作为参数

```python
@example_handler.got('name', 'age')
def _(name, age):
  print(f'Hello {name}! You are {age} years old.')
```

#### reject, finish

这两个方法仅用于在`handler`(见上面)和`condition_handler`(见上面)中调用

- 在`handler`中调用, 会中断`handler`运行并关闭`session`
- 在`condition_handler`中调用，
  - `reject`会中断`condition_handler`运行，并清空该`condition_handler`所需的键值数据，在下一次满足条件时会再次被调用
  - `finish`会中断`condition_handler`运行，该`condition_handler`不会再运行

#### 注意

- 为了使用自由度，`handler`、`receiver`、`condition_handler`中需要使用 ctx 或 session 时，请通过`from botoy.session import ctx, session`进行导入使用
- 正在等待的数据 watings 是用的 list 来储存，这意味这你可以等待多个相同的键值，但是数据时 dict 来储存，所以结果是数据被替换。建议避免使用同一个键值, 如果有需要，在获取到数据后马上清除该数据，或直接使用 pop 方法
- `handler`在 session 被新建后运行一次，`receiver`和`condition_handler`只有存在 session 时才会运行，且是依次运行
- 请不要注册需要同样数据的`condition_handler`, 否则可能会有灵异事件
- 可以通过`session.close()`方法关闭 session，但 session 的关闭只是一个标志，用于在获取时过滤。推荐使用`reject`或`finish`方法关闭 session，但只有在`handler`中调用才有关闭 session 的效果

## 示例

1. 查询模式，接收到内容为“查询”时开启查询模式，用户发送的每条信息都将作为关键字，并回复该关键字的查询结果

```python
{!../docs_src/session_search.py!}
```

## Prompt

少部分方法支持设置`prompt`参数，该参数具体见注释。其中支持的类型就是`Prompt`(`botoy.session.Prompt`)

这里提出是为了说明有这个东西。内容很少

用例:

```python
from botoy.session import Prompt

example_handler.finish(Prompt.group_picture(...))
```

**因为`OPQ`的宏系统很简单，所以这个功能不好实现也不好用**

#### 声明

该部分在 API 样子上有借鉴[nonebot](https://github.com/nonebot/nonebot2),
部分内容看起来类似，但具体使用是完全不同的
