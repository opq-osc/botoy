# 配置 (jconfig)

```python
from botoy import jconfig
```

框架推荐使用统一的配置文件来管理配置，文件为工作目录下的`botoy.json` 或 `botoy.local.json` 文件。

优先使用`botoy.local.json`, 注意这两个文件同时存在时，内容不会被合并。

框架当前保留配置如下：

```json
{!../botoy.json!}
```

`url` `qq`会被用于所有需要用到连接或机器人 qq 的场景的默认值，如：`Botoy`的`connection_url` 、`Action`的`url`和`qq`等。

优先级为: `指定参数值 > 配置文件 > 默认值`

# jconfig

框架提供`jconfig`与`botoy.json`进行交互，配置规则类似`vscode settings.json`（不熟悉也不要紧）

以下通过代码进行说明。(其中有部分配置项，为旧版 Botoy 参数，因为不影响此处演示，故未作修改)

假设 botoy.json 内容如下：

```json
{
  "host": "http://127.0.0.1",
  "port": 8086,
  "webhook": false,
  "webhook_post_url": "http://127.0.0.1:5000",
  "webhook_timeout": 20,

  "github.token": "github token",
  "github.username": "github username",
  "github.email": "github email",
  "github.issue.format": " gitub issue format",
  "github.issue.includeUrl": false,
  "github.pr.format": "github pr format",
  "github.pr.includeUrl": true
}
```

其中上面部分是框架专属配置，不需要说明。下面是假定的一个插件的配置，这里说明一下，该插件配置项的各项含义:

这是一个 GitHub 推送插件，有两个功能分别对应 issue 和 pr，token，username，eamil 是基础信息配置，issue 和 pr 有自己单独的配置项
format 表示推送格式，includeUrl 表示是否包括该项的网页地址

```python
{!../docs_src/jconfig.py!}
```

运行上面示例, botoy.json 内容变为

```json
{
  "host": "new host",
  "port": 8086,
  "webhook": false,
  "webhook_post_url": "http://127.0.0.1:5000",
  "webhook_timeout": 20,
  "github.token": "github token",
  "github.username": "github username",
  "github.email": "github email",
  "github.issue.includeUrl": true,
  "github.pr.format": "new github pr format",
  "github.pr.includeUrl": true
}
```
