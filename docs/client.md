# 客户端 (Botoy)

```python
from botoy import Botoy
```

`Botoy`类处理与本体的连接。该类实例化无需参数，各项属性需通过方法进行设置。

如所需参数，是否异步的详细信息请依靠你的 IDE/Editor 的提示进行查看。

## 属性

| 名称             | 类型  | 含义                    |
| ---------------- | ----- | ----------------------- |
| `connection_url` | `str` | opq websockets 连接地址 |

## 方法

| 名称              | 说明                                                                          |
| ----------------- | ----------------------------------------------------------------------------- |
| `set_url`         | 设置 opq websockets 连接地址                                                  |
| `load_plugins`    | 加载插件，必须显式调用该方法才会加载插件(插件仅仅是分文件/分模块提供接收函数) |
| `print_receivers` | 打印所有接收函数信息                                                          |
| `attach`          | 装饰并注册接收函数，直接使用实例对象本身 `@bot`                               |
| `connect`         | 连接 opq 服务端                                                               |
| `disconnect`      | 断开连接                                                                      |
| `wait`            | 阻塞等待至`disconnect`被调用                                                  |
| `run`             | 一键启动                                                                      |
| `run_as_server`   | 启动ws服务                                                                    |

!!!Tip

    框架默认实例化并导出了一个`Botoy`对象，可直接导入
    ```python
    from botoy imoprt bot
    ```

## 示例

```python
from botoy import bot

bot.set_url("localhost:8086") # 设置连接地址
bot.load_plugins() # 加载插件

@bot.attach # 使用attach方法注册接收函数
async def receiver_a():
    pass

@bot # 直接使用对象注册接收函数
def receiver_b(): # 框架推荐使用异步，但对于一些简单的场景，也可使用同步函数
    pass

bot.print_receivers() # 打印接收函数信息
bot.run() # 一键启动
```
