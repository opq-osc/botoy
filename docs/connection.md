# 其他方式连接服务端(接收消息)

首先说明所有发送获取等操作都是通过 http 方式，这也是唯一的方式。但获取信息可以有多种方式，一般是 socketio 连接服务端，这也是框架唯一封装的方式。

下面简单说一下如何使用其他方式进行连接。

前面的所有内容，比如配置，定义各类对象等方式都没有变化。`Botoy`对象提供了三个消息入口函数：
群消息`group_msg_handler`、好友消息`friend_msg_handler`、事件`event_handler`，
只要将消息对应传入这三个入口函数，即可处理所有逻辑。自带的`run`方法即是封装了 socketio client
的连接方式，获取消息再调用入口函数的步骤。所以，使用其他的方式连接也很简单。如 webhook 和 socketio server, 因为这两类方式很多，并没有进行封装。

- 入口函数参数为字典类型，必须是完整的消息结构

## webhook

### flask

```python
{!../docs_src/conn/flask_.py!}
```

### fastapi

```python
{!../docs_src/conn/fastapi_.py!}
```

## ws server

### flask socketio

```python
{!../docs_src/conn/flask_socketio_.py!}
```

### fastapi socketio

```python
{!../docs_src/conn/fastapi_socketio_.py!}
```
