# 接收函数装饰器

这个模块提供了一些常用操作的装饰器, 像判断文字中是否存在关键字、只处理特定的消息类型、忽略机器人自身的消息等等

## 装饰器

| 名称                    | 作用                                          | 适用的消息          |
| ----------------------- | --------------------------------------------- | ------------------- |
| equal_content           | 发送的内容与指定字符串相等时                  | GroupMsg, FriendMsg |
| in_content              | Content 字段包括指定字符串                    | GroupMsg, FriendMsg |
| from_these_groups       | 只接受这些群组的消息                          | GroupMsg            |
| from_these_users        | 仅接受来自这些用户的消息                      | GroupMsg, FriendMsg |
| ignore_botself          | 忽略机器人自身的消息                          | GroupMsg, FriendMsg |
| ignore_these_groups     | 不接受这些群组的消息                          | GroupMsg            |
| ignore_these_users      | 忽略这些人的消息                              | GroupMsg, FriendMsg |
| from_botself            | 只处理机器人自身的消息                        | GroupMsg, FriendMsg |
| startswith              | Content 以指定前缀开头                        | GroupMsg, FriendMsg |
| these_msgtypes          | 仅接受该些类型消息                            | GroupMsg, FriendMsg |
| with_pattern (即将移除) | 正则匹配 Content 字段                         | GroupMsg, FriendMsg |
| ensure_tempMsg          | 只接收私聊信息                                | FriendMsg           |
| ignore_tempMsg          | 忽略私聊信息                                  | FriendMsg           |
| from_phone              | 来自手机的消息(给自己发的)                    | FriendMsg           |
| from_admin              | 来自群管理员(列表包括群主)的消息              | GroupMsg            |
| queued_up               | 队列执行函数                                  |                     |
| on_regexp               | 正则匹配 Content 字段                         | GroupMsg, FriendMsg |
| ignore_admin            | 忽略来自群管理员(列表包括群主)的消息          | GroupMsg            |
| common_text             | 常见对文字消息的处理(不考虑私聊消息)          | GroupMsg, FriendMsg |
| need_action             | 自动创建 action 并作为接收函数第 2 个参数传入 |                     |

## 装饰器签名

```python
{!../docs_src/decorators_outline.py!}
```

## 示例

```python
{!../docs_src/decorators_example.py!}
```

## 注意

- 这个模块都是一些简单的封装，可以根据需要使用

- 每个装饰器的作用是重合关系

```python
    @deco.in_content('a')
    @deco.in_content('b')
```

表示要求消息中同时存在 a 和 b，而不是 a 或 b

- 在装饰器的第一行注释中，如果有 GroupMsg,
  FriendMsg 表示可用于群消息和好友消息接收函数，如果只有 GroupMsg 表示只能用于群消息接收函数，以此类推

- 因为消息类型很多，比如图片视频语音，所以有些判断会很麻烦或者不好处理,
  对函数有疑问的请看注释或查看源码

- 部分装饰器有 func 参数，该参数永远都不需要指定!
