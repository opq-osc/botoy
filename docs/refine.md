# ~~精细化消息~~(模块已废弃)

## 提取准确信息的 refine 函数

默认传递的上下文对象只包含该消息的固定字段，也就是不管哪种，都会包含的东东。
上面说过图片、文字、语音甚至红包消息等消息的不同在 Content 字段中，该字段永远是 str 类型，对于文本消息，该字段就是消息原文，
对其他消息来说，该字段是一个 json 格式的映射，如果需要处理这些数据，就需要自己通过解码 json 获得，
提取这些数据，如果是好友和群消息，不会特别麻烦，但如果处理含有特别多不同字段的事件类型的消息那就....
很明显这是一个常用操作，为了避免重复劳动，所以提供了一系列 `refine_?` 函数用来进一步解析数据。

这些函数位于模块`refine`中

其中每一个函数对应一种消息类型或场景，如果消息类型与该函数所期望处理的类型一致,
则会返回一个新的上下文对象,新对象包含了更详尽的属性。
如果消息类型不匹配，则返回 None，所以 refine 函数也能起判断(类型筛选)的作用

通过函数名称自行选择所需的函数

## 一览

| 名称(省略 refine\_前缀)        | 作用                                | 对应的类型                    | 备注                                         |
| ------------------------------ | ----------------------------------- | ----------------------------- | -------------------------------------------- |
| group_revoke_event_msg         | 群成员撤回消息事件                  | \_GroupRevokeEventMsg         |                                              |
| group_exit_event_msg           | 群成员退出群聊事件                  | \_GroupExitEventMsg           |                                              |
| group_join_event_msg           | 某人进群事件                        | \_GroupJoinEventMsg           |                                              |
| friend_revoke_event_msg        | 好友撤回消息事件                    | \_FriendRevokeEventMsg        |                                              |
| friend_delete_event_msg        | 删除好友事件                        | \_FriendDeleteEventMsg        |                                              |
| group_adminsysnotify_event_msg | QQ 群系统消息通知(加群申请在这里面) | \_GroupAdminsysnotifyEventMsg |                                              |
| group_shut_event_msg           | 群禁言事件                          | \_GroupShutEventMsg           |                                              |
| group_admin_event_msg          | 管理员变更事件                      | \_GroupAdminEventMsg          |                                              |
| voice_group_msg                | 群语音消息                          | \_VoiceGroupMsg               |                                              |
| video_group_msg                | 群视频消息                          | \_VideoGroupMsg               |                                              |
| pic_group_msg                  | 群图片/表情包消息                   | \_PicGroupMsg                 | GroupPic 字段是列表，每项是\_GroupPic 类型   |
| RedBag_group_msg               | 群红包消息                          | \_RedBagGroupMsg              |                                              |
| voice_friend_msg               | 好友语音消息                        | \_VoiceFriendMsg              |                                              |
| video_friend_msg               | 好友视频消息                        | \_VideoFriendMsg              |                                              |
| pic_friend_msg                 | 好友图片/表情包消息                 | \_PicFriendMsg                | FriendPic 字段是列表，每项是\_FriendPic 类型 |
| RedBag_friend_msg              | 好友红包消息                        | \_RedBagFriendMsg             |                                              |
| file_friend_msg                | 好友文件消息                        | \_FriendFileMsg               |                                              |
| reply_friend_msg               | 好友回复消息                        | \_ReplyFriendMsg              |                                              |
| at_group_msg                   | 群回复消息                          | \_AtGroupMsg                  |                                              |
| reply_group_msg                | 群回复消息                          | \_ReplyGroupMsg               |                                              |
| file_group_msg                 | 群文件消息                          | \_GroupFileMsg                |                                              |

**导入所需的类型配合类型注解获得代码提示**

暂时没有处理 AT 消息，后续将增加,
现在有大佬贡献了相关代码，具体使用请结合实际情况。

示例:

```python
{!../docs_src/refine_example.py!}
```
