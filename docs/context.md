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

`GropuMsg`, `FriendMsg` 提供了大量属性或方法可用于实际的业务逻辑中，并且具备详细的注释，请依靠代码补全查看。
