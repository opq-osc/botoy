# Mahiro

```python
from botoy import Mahiro
```

`Mahiro`是社区 js sdk，botoy 可以通过接入 mahiro 获得其插件管理功能。

## 使用

### 配置项

`botoy.json`

```json
{
  "mahiro.listen_url": "py作为服务端监听地址，默认为：0.0.0.0:8099",
  "mahiro.server_url": "mahiro服务端地址，默认为：localhost:8098"
}
```

### 运行

```python
from botoy import Mahiro

mahiro = Mahiro()
mahiro.load_plugins()
mahiro.print_receivers()
mahiro.listen()
```
