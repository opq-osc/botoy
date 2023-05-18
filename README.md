# botoy

[![QQ Group](https://img.shields.io/badge/QQ%E7%BE%A4-856337734-important?style=flat-square&logo=tencentqq)](https://jq.qq.com/?_wv=1027&k=K8iQy7i7)

[![pypi](https://img.shields.io/pypi/v/botoy?style=flat-square 'pypi')](https://pypi.org/project/botoy/)
[![python](https://img.shields.io/badge/python-3.8+-blue 'python')](https://pypi.org/project/botoy/)
[![Lines of code](https://img.shields.io/tokei/lines/github/opq-osc/botoy?label=lines&style=flat-square)](https://github.com/opq-osc/botoy)
[![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/opq-osc/botoy?style=flat-square)](https://github.com/opq-osc/botoy)
[![LICENSE](https://img.shields.io/github/license/opq-osc/botoy?style=flat-square)](https://github.com/opq-osc/botoy/blob/main/LICENSE)

对机器人框架[OPQ](https://github.com/OPQBOT/OPQ/)接口的 Python 封装,
因为功能模块耦合度低, 所以你可以完全使用该框架开发，也可以选取需要的内容到自己的项目中

---

## 安装

```shell
pip install botoy -i https://pypi.org/simple --upgrade
```

## 示例

如果你配置好了 OPQ，并且配置保持默认(bot 连接地址`http://127.0.0.1:8086`)，
下面示例可实现在收到群消息内容为 `test` 时回复 `ok`

新建文件 `bot.py`

```python
from botoy import bot, ctx, S

@bot
async def test():
    if ctx.g and ctx.g.text == 'test':
        await S.text('ok')

bot.print_receivers()
bot.run()
```

运行 `python bot.py`

```
+------+--------+-------+----------------+
| Name | Author | Usage |      Meta      |
+------+--------+-------+----------------+
| test |        |       | test.py line 4 |
+------+--------+-------+----------------+
ℹ️ 04-15 19:21:58 INFO 连接中[ws://localhost:8086/ws]...
✔️ 04-15 19:21:58 SUCCESS 连接成功!
```

# [文档](https://botoy.readthedocs.io/)

<!-- # [简单例子](https://github.com/opq-osc/botoy-plugins) -->

<!-- # [插件模板](https://github.com/opq-osc/botoy-plugin-template) -->

# 感谢

[yuban10703](https://github.com/yuban10703)
[milkice](https://github.com/milkice233)

# LICENSE

MIT
