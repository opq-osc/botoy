# 插件化

## 启用

启用就是显式调用`Botoy.load_plugins`方法。

插件目录为`plugins`

## 定义插件

所有在 plugins 目录下的`py`文件以及模块（包含`__init__.py`的文件夹）都会被当作插件导入。

严格来说插件的作用仅仅是提供接收函数`receiver`，所以要在插件内定义`receiver`

有两种方法定义`receiver`

### `mark_recv`

`mark_recv`用于将**可调用**对象标记为`receiver`。

仍然通过代码示例进行说明。

1. 收到群消息 test 回复 ok

```python
from botoy import S, ctx, mark_recv


async def test():
    if g := ctx.group_msg:  # 仅当为群消息
        if g.text == "test":  # 接收信息内容为 test
            await S.text("ok")  # 根据场景发送文本


mark_recv(test, name="测试", author='tester', usage='群聊中发送 test')  # 插件信息仅用于控制台显示, 可选
```

2. 在群聊中发送 hello，机器人回复 hello。私聊 hello 时，机器人回复 hi

```python
from botoy import S, ctx, mark_recv


async def hello():
    if g := ctx.g:  # ctx.g == ctx.group_msg
        if g.text == "hello":
            await S.text("ok")


async def hi():
    if f := ctx.f:  # ctx.f == ctx.friend_msg
        if f.text == 'hello':
            await S.text('hi')


# 运算符+快速添加多个接收函数
_ = mark_recv + hello + hi
# 也可以调用mark_recv多次
# mark_recv(hello)
# mark_recv(hi)
# 运算符调用使用数组形式传递位置参数 name, author, usage
# _ = mark_recv + hello + (hi, 'hi friend')
```

3. mark_recv 可以注册各种类型的可调用对象

```python
from botoy import mark_recv


class A:
    @classmethod
    def class_method(cls):
        pass

    def object_method(self):
        pass

    @classmethod
    async def async_class_method(cls):
        pass

    async def async_object_method(self):
        pass


lambda_function = lambda: None


def sync_function():
    pass


async def async_function():
    pass


a = A()

_ = (
    mark_recv
    + (A.class_method, '类方法')
    + (a.object_method, "实例方法")
    + (lambda_function, '匿名函数')
    + (sync_function, '同步函数')
    + (async_function, '异步函数')
    + (a.async_class_method, '异步类方法')
    + (a.async_object_method, '异步实例方法')
)

```

### `r_`命名前缀

将函数以`r_`作为前缀命令即可。这样方便点，但是不方便设置`receiver`信息

!!!Tip

    插件信息默认为：

    - `name`: receiver的__name__
    - `author`: 空
    - `usage`: receiver的__doc__
