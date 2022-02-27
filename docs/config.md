# 配置

**本框架对所有配置项都没有进行严格的校验，默认你知道如何配置，配置类型，并且正确配置**。
建议不需要用的就别配置

配置可以通过实例化时通过传参完成，因为客户端实例只有一个，所以并不麻烦，但是后面要用到动作发送
API 时，就需要频繁的定义，这十分麻烦，造成这个的主要原因就是你的 bot 端没有按默认设置运行，一般情况下端口(默认为 8888)
有时 IP 也会根据各自有所不同

所以可以新建一个配置文件，固定为`botoy.json`定义配置，配置项和默认值如下

环境变量`BOTOY_HOST`, `BOTOY_PORT` 存在的情况下，将分别作为 host, port 的默认值

```json
{!../botoy.json!}
```

配置项在前面客户端部分有说明

后三项与 webhook 功能有关，后续说明

请按需配置

约定：如果存在配置文件的同时在实例化对象时也传入了参数，会优先使用指定的参数值，
优先级为: `指定参数值 > 配置文件 > 默认值`

**强烈建议使用配置文件**, 并且建议将`botoy.json`作为统一的配置文件用于其他功能的配置

# jconfig

不仅框架自身配置使用 botoy.json,
同时推荐插件也使用 botoy.json 作为配置文件。使用 jconfig 可以很好的对配置进行操作

假设 botoy.json 内容如下：

```json
{
  "host": "http://127.0.0.1",
  "port": 8888,
  "group_blacklist": [],
  "friend_blacklist": [],
  "blocked_users": [],
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
{!../docs_src/jconfig.py}
```

运行上面示例, botoy.json 内容变为

```json
{
  "host": "new host",
  "port": 8888,
  "group_blacklist": [],
  "friend_blacklist": [],
  "blocked_users": [],
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

!!!提示

    如果你是vscode用户，那么，这种配置方式应该很熟悉了(settings.json)

# 配置注释问题

因为收益低于成本，所以抛弃了使用 jsonc 等等其他配置文件方案，注释通过字段设置

如

```json
{
  "host": "127.0.0.1",
  "host_comment": "机器人主机地址"
}
```

具体方式很多样，自己选择
