# 辅助函数 `contrib`

`botoy.contrib`模块封装了部分常用的操作函数

## `file_to_base64` 获取文件 base64 编码

## `get_cache_dir` 获取框架统一的缓存目录

```python
from pathlib import Path

from botoy.contrib import get_cache_dir

assert get_cache_dir('botoy') == Path('botoy-cache/botoy')
assert get_cache_dir('test') == Path('botoy-cache/test')
```

该函数在程序任何位置调用都是同一结果

## `download` 一个简单通用的下载函数

## `to_async` 将同步函数包装为异步函数的装饰器

防止在使用异步时被耗时很长的同步函数堵住

```python
import time

from botoy.contrib import to_async

@to_async
def sleep(sec):
    time.sleep(sec)  # 模拟一个同步耗时操作

await sleep(5)
```

## `async_run` 将同步函数以异步方法执行

和`to_async`装饰器基本一致

```python
import time

from botoy.contrib import async_run

await async_run(time.sleep, 5)  # 模拟一个同步耗时操作
```

## `sync_run` 同步执行异步函数

```python
async def hello(name=None):
    if name:
        return f'Hello {name}'
    return 'Hello'


print(sync_run(hello()))  # Hello
print(sync_run(hello('World')))  # Hello World
```

## `RateLimit` 调用速率控制

```python
{!../docs_src/ratelimit.py!}
```

- 每个函数只能对应单独的`RateLimit`对象

## `Switcher`, `SwitcherManager` 开关

### `Switcher` 基础的开关类

```python
from botoy.contrib import Switcher

switcher = Switcher(True) # 设置初始状态为开启

assert switcher.enabled == True

switcher.disable()
assert switcher.enabled == False

switcher.enable()
assert switcher.enabled == True

switcher.toggle()
assert switcher.enabled == False

assert bool(switcher) == switcher.enabled
```

### `SwitcherManager` 开关管理器

```python
from botoy.contrib import SwitcherManager

# 创建一个标识为 test 的开关管理器，开关的默认状态为 True
sm = SwitcherManager('test', True)

# 获取一个开关, 与 用户123456 绑定
switcher_123456 = sm.of(id=123456) # !!! 不同的id不同的开关 !!!

# 获取默认开关
switcher = sm.of()
```

!!!tip

    目前数据储存在内存中，所以启动就是重置。实用性并不高。后续会添加缓存功能。
