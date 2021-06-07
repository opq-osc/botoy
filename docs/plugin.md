# 插件化

## 启用

开启插件功能，定义客户端时将参数`use_plugins`设置为`True`即可

插件以模块的方式来提供接收函数，分为两种，单文件和文件夹

插件目录为`plugins`

单文件: bot_pluginA.py (插件标记为 pluginA)

包：bot_pluginB (插件标记为 pluginB)

包支持子目录提供插件同样支持包和文件夹形式, **最多二级子目录**

bot_pluginB_sub1.py (插件标记为 pluginB.sub1)

bot_pluginB_sub2 (插件标记为 pluginB.sub2)

见下列目录树:

```
plguins
├── bot_a.py
├── bot_b.py
└── bot_c
    ├── bot_c_1
    ├── bot_c_2.py
    └── bot_c_3.py
```

则插件为：`a`, `b`, `c.c_1`, `c.c_2`, `c.c_3`

## 插件要求

插件作为模块，从中导入消息接收函数, 接收函数命名

|                    |          |
| ------------------ | -------- |
| receive_group_msg  | 群消息   |
| receive_friend_msg | 好友消息 |
| receive_events     | 事件消息 |

!!!tip

    1. 插件命名或接收函数命名有误都不会影响程序运行，因为根本不会导入或调用
    2. 接收函数参数有且只有一个，与使用client方法装饰器绑定的接收函数一样

要求

1.  文件(或文件夹)名需以`bot_`开头

2.  如果使用文件夹，接收函数需放在`__init__.py`中

## 插件管理器的方法和属性

假设 `bot = Botoy(123)`

方法：

_现在已删除了所有管理插件的快捷方法, 需要管理需要访问`bot.plugMgr`对象的方法_

|                |              |
| -------------- | ------------ |
| load_plugins   | 加载插件     |
| reload_plugins | 重载插件     |
| reload_plugin  | 重载指定插件 |
| disable_plugin | 停用指定插件 |
| enable_plugin  | 启用指定插件 |

同时有以下属性:

|                  |                      |
| ---------------- | -------------------- |
| all_plugins      | 返回当前所有插件信息 |
| disabled_plugins | 已停用的插件         |
| enabled_plugins  | 已启用的插件信息     |

## 定义插件信息

### 帮助

插件的文档注释就是该插件的帮助(建议显示指定`__doc__`变量)

`plugMgr`的相关方法和属性

- 属性`help` 所有插件的帮助信息，是一个框架整理好的字符串
- 方法`get_plugin_help` 获取指定插件的帮助信息

### 名称

插件的`__name__`变量，可以在插件显示指定

!!!tip

    以上所有方法或属性的具体用法或含义请查看注释
