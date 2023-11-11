# 消息上下文 (ctx)

```python
from botoy import ctx
```

消息上下文只能在接收函数中使用，其包含当前消息的所有内容。

- `ctx.data`为当前消息的原始数据。
- `ctx.group_msg`(alias: `ctx.g`)为群消息(`GroupMsg`)，非群消息时为`None`
- `ctx.friend_msg`(alias: `ctx.f`)为好友消息(`FriendMsg`)，非好友消息时为`None` (包括私聊)
- `ctx.event_msg`(alias: `ctx.e`)为事件消息(`EventMsg`)，非事件消息时为`None`

## 属性和方法一览

**仅列出常用的, 更多信息可以通过补全列表查看对应注释进行了解。（存在不同属性表示相同含义，是正常的）**

### `BaseMsg`

`GroupMsg` 和 `FriendMsg` 继承自`BaseMsg`，故具有以下相同属性和方法。

| 属性           | 说明               |
| -------------- | ------------------ |
| `images`       | 图片列表           |
| `voice`        | 语音               |
| `video`        | 短视频             |
| `text`         | 文字内容           |
| `is_from_self` | 是否来自机器人自身 |
| `sender_uin`   | 发送者 QQ 号       |
| `sender_nick`  | 发送者的昵称       |
| `from_type`    | 消息来源的类型     |
| `bot_qq`       | 机器人 QQ 号       |

| 方法         | 说明                                                  |
| ------------ | ----------------------------------------------------- |
| `text_match` | 使用 re 模块中 match 方法匹配消息中文字内容的快捷方法 |

### `GroupMsg` 群消息

| 属性              | 说明             |
| ----------------- | ---------------- |
| `from_group`      | 群组 ID          |
| `from_group_name` | 群组名称         |
| `from_user`       | 发送者 QQ 号     |
| `from_user_name`  | 发送者昵称       |
| `at_list`         | 被艾特的用户列表 |
| `is_at_bot`       | 是否艾特了机器人 |

| 方法         | 说明               |
| ------------ | ------------------ |
| `revoke`     | 撤回该消息         |
| `is_at_user` | 判断是否艾特某用户 |

### `FriendMsg` 好友消息(私聊)

| 属性             | 说明                                           |
| ---------------- | ---------------------------------------------- |
| `from_user`      | 发送者的 QQ 号                                 |
| `from_user_name` | 发送者的昵称                                   |
| `is_private`     | 判断消息是否为私聊                             |
| `from_group`     | 发送者的群号, 仅私聊存在，否则使用该属性将报错 |
| `is_from_phone`  | 判断消息是否来自手机                           |

### `EventMsg` 事件消息

暂时没封装事件消息，目前可使用 `ctx.data`（原始数据）自行处理

例：处理退群事件

```python
packet = ctx.data['CurrentPacket']
if packet['EventName'] == 'ON_EVENT_GROUP_EXIT':
    ev = packet['EventData']
    uid = ev['Event']['Uid'] # 退群者
    group = ev['MsgHead']['ToUid'] # 群号
```
