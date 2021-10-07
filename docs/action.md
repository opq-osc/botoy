# 动作(API)

这个类封装了部分 webapi, 使用前请简单了解下 bot 端的 webapi 使用方法

## 初始化

```python
from botoy import Action

action = Action(qq=123456)
```

| 参数    | 是否必选 | 作用                                                                      |
| ------- | -------- | ------------------------------------------------------------------------- |
| qq      | 否       | 执行操作的 qq 号, 如果未传，则尝试读取配置文件中的`qq` 字段，找不到则报错 |
| port    | 否       | bot 端端口                                                                |
| host    | 否       | bot 端 ip                                                                 |
| timeout | 否       | 等待 webapi 响应的延时,默认为 20                                          |

port 和 host 的含义和 Botoy 实例中的一致

如果是在接收函数中，可以通过类方法`Action.from_ctx`获取`action`,
该方法会处理`ctx`中的`_host`和`_port`属性

## Action.baseRequest 方法

这是最基础的请求方法，封装了错误处理和提示

参数有:

| 参数名称 | 作用                            | 类型 |
| -------- | ------------------------------- | ---- |
| method   | http 请求类型                   | str  |
| funcname | api 需要执行的类型              | str  |
| path     | 请求路径, 如:`/v1/LuaApiCaller` | str  |
| payload  | 需要提交的 json 数据            | dict |
| params   | URL 中的参数                    | dict |

- params 默认会添加 funcname 和 qq

## Action.post 和 Action.get 方法

基于 baseRequest 方法，又封装了常用的 post 和 get 方法

### post 接受的参数

- funcname: ~
- payload: ~
- params: 默认为 None
- path: 默认为 `/v1/LuaApiCaller`

### get 接受的参数

- funcname: ~
- params: 默认为 None
- path: 默认为 `/v1/LuaApiCaller`

## 方法一览

基于以上方法，封装了部分常用的 API

| 名称                | 作用                             |
| ------------------- | -------------------------------- |
| sendPhoneText       | 给手机发文字                     |
| sendFriendText      | 发送好友文本消息                 |
| sendFriendVoice     | 发送好友语音消息                 |
| sendFriendPic       | 发送好友图片消息                 |
| senfFriendXml       | 发送好友 Xml 类型消息            |
| sendGroupText       | 发送群文字消息                   |
| sendGroupVoice      | 发送群语音                       |
| sendGroupPic        | 发送群图片                       |
| sendGroupJson       | 发送群 Json 类型信息             |
| sendGroupXml        | 发送群 Xml 类型信息              |
| sendPrivateText     | 发送私聊文字消息                 |
| sendPrivateVoice    | 发送私聊语音                     |
| sendPrivatePic      | 发送私聊图片                     |
| sendPrivateXml      | 发送私聊 Xml 类型信息            |
| replyGroupMsg       | 发送回复消息,回复群消息          |
| replyFriendMsg      | 发送回复消息,回复好友消息,不好用 |
| getUserInfo         | 获取用户信息                     |
| getCookies          | 获取 cookies                     |
| getUserList         | 获取好友列表                     |
| getGroupList        | 获取群聊列表                     |
| getGroupMembers     | 获取群成员列表                   |
| getGroupAdminList   | 获取群管理列表                   |
| setUniqueTitle      | 设置群成员头衔                   |
| modifyGroupCard     | 修改群名片                       |
| shutAllUp           | 开启或关闭全员禁言               |
| shutUserUp          | 设置群成员禁言                   |
| likeUser            | 点赞                             |
| setGroupAnnounce    | 设置群公告                       |
| toggleGroupAdmin    | 设置或取消群管理员               |
| revokeGroupMsg      | 撤回群消息                       |
| inviteUserJoinGroup | 拉人入群                         |
| joinGroup           | 加入群聊                         |
| exitGroup           | 退出群聊                         |
| driveUserAway       | 移出群聊                         |
| getClusterInfo      | 获取当前集群信息                 |
|                     | 搜索群组                         |
| refreshKeys         | 刷新 key 二次登陆                |
|                     | 添加好友                         |
|                     | 处理好友请求                     |
| logout              | 退出指定 qq                      |
|                     | 获取登录二维码的 base64 编码     |
| getFriendFileURL    | 获取好友文件下载链接             |
| getGroupFileURL     | 获取群文件下载链接               |
| repostVideo2Group   | 转发视频到群聊                   |
| repostVideo2Friend  | 转发视频给好友                   |
| getVideoURL         | 获取短视频链接                   |
| sendGroupTeXiaoText | 发送群组特效文本消息             |
| getSummaryCard      | 获取企鹅卡片资料                 |
| poke                | 戳一戳                           |
| uploadGroupFile     | 上传群文件                       |
| groupJoinAuth       | 入群审核                         |

- 除特殊说明，API 返回的都是字典类型，如果出错则返回空字典
- 没有方法名的表示还未封装，说明前面带\*号的表示还不完善

## 语法糖

### 函数

**仅能在群消息和好友消息接收函数中使用, 事件类型不支持使用**

函数位于模块 sugar 中

| 函数名  | 作用         |
| ------- | ------------ |
| Text    | 发送文字消息 |
| Picture | 发送图片消息 |
| Voice   | 发送语音消息 |

- 函数会自动根据消息上下文 ctx 判断需要发送的对象

- 所有都支持三种情况:
  群消息，好友消息，私聊消息(临时会话)

- 只有 Text 支持对来自手机的消息进行回复

### S

S 方法相比函数调用更为简洁

| 方法名  | 作用         |
| ------- | ------------ |
| S.text  | 发送文字消息 |
| S.image | 发送图片消息 |
| S.voice | 发送语音消息 |

各个方法注释还算完善，简单说明几个需要注意的地方

image 和 voice 都有一个参数 data, 该参数可以为

    1. 字符串， 表示 url，base64，MD5, file path
    2. 字符串列表， 表示发送 MD5
    3. Path 对象，表示 file path
    4. bytes => base64
    5. BytesIO => base64
    6. BinaryIO => base64

默认会自动判断内容的发送类型，你也可以显示指定参数 type, 允许值为 S.TYPE\_?

自动判断规则大概为：

    - http:// 或 https:// 开头的字符串会被判断为 url
    - 长度为24且==结尾的字符串, 字符串列表会被判断为base64
    - 长度小于1000的字符串且该字符串指向存在的文件，Path对象会被判断为文件路径（path）
    - 以上的缺省情况，如果字符串符合base64编码, 会被判断为base64

    以上情况均不满足(正确传入数据，就不可能发生)，则会报错。

voice 不支持 MD5, 否则会报错

以上方法也只能在接收函数中调用，但是提供了方法`S.bind`显示绑定
`ctx`，该方法返回新的`S`(new_S),
new_S 的发送方法和原来一致，但不局限于接收函数内调用

!!!使用建议

    首先看 Action 是否已经封装了 API，如果没封装，根据 webapi 的请求格式使用 post 和 get 以及 baseRequest 构建请求

!!!更多用法
