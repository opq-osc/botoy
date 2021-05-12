# botoy

[![pypi](https://img.shields.io/pypi/v/botoy?style=flat-square 'pypi')](https://pypi.org/project/botoy/)
[![python-version](https://img.shields.io/pypi/pyversions/botoy?style=flat-square)](https://pypi.org/project/botoy/)

对机器人框架[OPQ](https://github.com/OPQBOT/OPQ/)接口的 Python 封装,
因为功能模块耦合度低,
所以你可以完全使用该框架开发，也可以选取需要的内容到自己的项目中

---

## 安装

```shell
pip install botoy -i https://pypi.org/simple --upgrade
```

## 示例

如果你配置好了 OPQ，并且配置保持默认(bot 连接地址`http://127.0.0.1:8888`)，下面一行代码即可监听消息，并在收到群消息或好友消息内容为 test 时回复 ok

```python
__import__('botoy').Botoy().on_group_msg(lambda ctx: __import__('botoy').Action(ctx.CurrentQQ).sendGroupText(ctx.FromGroupId, 'ok') if ctx.Content == 'test' else None).on_friend_msg(lambda ctx: __import__('botoy').Action(ctx.CurrentQQ).sendFriendText(ctx.FromUin, 'ok') if ctx.Content == 'test' else None).run()
```

# [文档](https://botoy.readthedocs.io/)

# [简单例子](https://github.com/opq-osc/botoy-plugins)

# 感谢

[yuban10703](https://github.com/yuban10703)
[milkice](https://github.com/milkice233)

# LICENSE

MIT
