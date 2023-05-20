# 发送操作 (Action)

```python
from botoy import Action
```

该类封装了 opq webapi。

注意：该类全局每次请求的间隔默认在 0.5s - 2s 之间，注意是全局，不是单个实例。

## 初始化

| 参数    | 是否必选 | 作用                             |
| ------- | -------- | -------------------------------- |
| qq      | 否       | 执行操作的 qq 号                 |
| url     | 否       | bot 端 url                       |
| timeout | 否       | 等待 webapi 响应的延时,默认为 20 |

qq 如果未传，则尝试读取配置文件中的`qq` 字段。

如果未配置 qq 字段，将从服务端自动获取 qq 列表并选择一个用于调用接口，具有随机性。

## `baseRequest` 方法

最基础的请求方法，封装了错误处理和提示

参数有:

| 参数名称 | 作用                            | 类型 |
| -------- | ------------------------------- | ---- |
| method   | http 请求类型                   | str  |
| funcname | api 需要执行的类型              | str  |
| path     | 请求路径, 如:`/v1/LuaApiCaller` | str  |
| payload  | 需要提交的 json 数据            | dict |
| params   | URL 中的参数                    | dict |
| timeout  | 请求超时时间                    | int  |

- params 默认会添加 funcname 和 qq

## `post` 和 `get` 方法

基于 baseRequest 方法，又封装了常用的 post 和 get 方法

### post 接受的参数

- funcname: 默认为`MagicCgiCmd`
- payload: ~
- params: 默认为 None
- path: 默认为 `/v1/LuaApiCaller`
- timeout: 超时时间

### get 接受的参数

- funcname: ~
- params: 默认为 None
- path: 默认为 `/v1/LuaApiCaller`
- timeout: 超时时间

## 方法一览

### 一般方法

| 名称      | 作用                                                                                  |
| --------- | ------------------------------------------------------------------------------------- |
| `set_url` | 设置 opq api 地址                                                                     |
| `set_qq`  | 设置发送请求机器人 qq 参数                                                            |
| `close`   | 由于是异步操作，需要手动进行关闭。可使用`with`语法自动关闭。`with Action() as action` |

基于`baseRequest`, `get`, `post`方法，封装了以下方法。

| 名称                    | 作用                                                                |
| ----------------------- | ------------------------------------------------------------------- |
| `sendPhoneText`         | 给手机发文字                                                        |
| `sendFriendText`        | 发送好友文本消息                                                    |
|                         | 发送好友语音消息                                                    |
| `sendFriendPic`         | 发送好友图片消息                                                    |
|                         | 发送好友 Xml 类型消息                                               |
| `sendGroupText`         | 发送群文字消息                                                      |
| `at`                    | 仅 at 群成员的空消息                                                |
|                         | 发送群语音                                                          |
|                         | 发送群图片                                                          |
| `sendGroupPic`          | 发送群多图                                                          |
|                         | 发送群 Json 类型信息                                                |
|                         | 发送群 Xml 类型信息                                                 |
| `sendPrivateText`       | 发送私聊文字消息                                                    |
|                         | 发送私聊语音                                                        |
| `sendPrivatePic`        | 发送私聊图片                                                        |
|                         | 发送私聊 Xml 类型信息                                               |
| `replyGroupMsg` `reply` | 发送回复消息,回复群消息                                             |
|                         | 发送回复消息,回复好友消息,不好用                                    |
|                         | 获取用户信息                                                        |
|                         | 获取 cookies                                                        |
|                         | 获取好友列表                                                        |
| `getGroupList`          | 获取群聊列表                                                        |
| `getGroupMembers`       | 获取群成员列表                                                      |
| `getGroupAdminList`     | 获取群管理列表                                                      |
| `getAllBots`            | 获取该 OPQ 登陆的所有 QQ 列表                                       |
|                         | 设置群成员头衔                                                      |
|                         | 修改群名片                                                          |
|                         | 开启或关闭全员禁言                                                  |
|                         | 设置群成员禁言                                                      |
|                         | 点赞                                                                |
|                         | 设置群公告                                                          |
|                         | 设置或取消群管理员                                                  |
| `revokeGroupMsg`        | 撤回群消息                                                          |
| `revoke`                | 撤回群消息, revokeGroupMsg 的便捷操作，直接传入消息 `GroupMsg` 即可 |
|                         | 拉人入群                                                            |
|                         | 加入群聊                                                            |
|                         | 退出群聊                                                            |
|                         | 移出群聊                                                            |
| `getClusterInfo`        | 获取当前集群信息                                                    |
|                         | 搜索群组                                                            |
|                         | 刷新 key 二次登陆                                                   |
|                         | 添加好友                                                            |
|                         | 处理好友请求                                                        |
|                         | 退出指定 qq                                                         |
|                         | 获取登录二维码的 base64 编码                                        |
|                         | 获取好友文件下载链接                                                |
|                         | 获取群文件下载链接                                                  |
|                         | 转发视频到群聊                                                      |
|                         | 转发视频给好友                                                      |
|                         | 获取短视频链接                                                      |
|                         | 发送群组特效文本消息                                                |
|                         | 获取企鹅卡片资料                                                    |
|                         | 戳一戳                                                              |
|                         | 上传群文件                                                          |
|                         | 入群审核                                                            |
|                         | 上传群图片获取图片信息                                              |
|                         | 上传头像                                                            |
|                         | 打开红包                                                            |
| `upload`                | 上传资源文件                                                        |

**如何使用，遇到问题如何解决？**

1. 妥善使用代码提示，查看可用方法
2. 认真查看注释，正确传递参数
3. 阅读 opq api 文档，了解大概
4. 遇到问题先用调试工具手动调用 api 确定是否为风控等情况

!!!Tip

    框架默认导出了一个`Action`对象
    ```python
    from botoy import action
    ```
