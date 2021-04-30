# WebHook 数据上报

## 配置

```json
{
  "webhook": false,
  "webhook_post_url": "http://127.0.0.1:5000",
  "webhook_timeout": 20
}
```

开启 webhook 功能需要设置配置项 webhook 为 true

另一个必选配置为 `webhook_post_url`(默认为`http://127.0.0.1:5000`) , 收到消息后会向该地址发送 POST 请求，推送数据格式为 Json，内容与 bot 端 发送过来的一致。

配置项 webhook_timeout 是指发送 post 请求到指定的地址，等待响应的时间

!!! tip

    该功能就是内置的三个接收函数，目前支持推送消息，后续视情况增加对响应结果的处理
