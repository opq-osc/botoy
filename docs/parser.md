# 消息解析

该模块封装对消息的解析操作，使用`pydantic`解析，有较好的类型提示。

**解析非文本消息的 Content 字段**

```python
from botoy.parser import group as gp # 群消息(GroupMsg)相关解析
from botoy.parser import friend as fp # 好友消息(FriendMsg)相关解析
from botoy.parser import event as ep # 事件(EevntMsg)相关解析
```

该模块很简单，看示例即可, 根据补全提示操作即可

```python
{!../docs_src/parser.py!}
```

当前可解析信息

## 群消息(GroupMsg)

|       |      |
| ----- | ---- |
| at    | 艾特 |
| reply | 回复 |
| pic   | 图片 |
| voice | 语音 |
| video | 视频 |
| file  | 文件 |

## 好友消息(FriendMsg)

|       |      |
| ----- | ---- |
| reply | 回复 |
| pic   | 图片 |
| voice | 语音 |
| video | 视频 |
| file  | 文件 |

## 事件(EventMsg)

|                      |            |
| -------------------- | ---------- |
| group_revoke         | 群撤回     |
| group_exit           | 用户退群   |
| group_join           | 新用户加群 |
| group_shut           | 禁言       |
| group_admin          | 群管理变更 |
| group_adminsysnotify | 加群申请   |
| friend_revoke        | 好友撤回   |
| friend_delete        | 好友删除   |
