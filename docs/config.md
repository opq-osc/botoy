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

# jconfig(Config())

`jconfig`是预先实例化的`Config`对象,

该对象可以便捷地访问**配置文件**`botoy.json`内设置的各项数据

```python
from botoy import jconfig
# from botoy.config import jconfig
```

- 方法`get_jconfig`, 获取配置项，未设置则为 `None`
- 通过`.`获取配置项，如`jconfig.host`, `jconfig.port`, 未设置则为 `None`

可以把 config 当作一个字典，这两种获取数据的方式就是字典的 get 方法

## get_section

前面的两种方式获取的数据都是基本类型，后续的操作都与 Config 无关，当配置多起来时，每个插件还可能有
相同的数据，此时配置会很乱，获取也会麻烦很多。`get_section`用来减轻这一问题

获取该字段所对应的数据

- 如果数据是字典类型，则返回一个新的 Config 对象，新的 Config 的方法对该数据进行处理
- 如果是其他类型数据，将直接返回
- 不存在则返回 None

例如 botoy.json 为

```json
{
    "A": {
        "B": "value of B"
        "C": ["item1", "item2"]
    }
}
```

那么

```python
config = Config()

assert config.A == {"B":"value of B", "C": ["item1", "item2"]}
assert config.A["B"] == "value of B"

section_a = config.get_section("A")
assert section_a.B == "value of B"

section_a_b = section_a.get_("B")
assert section_a_b == "value of B"

section_a_c = section_a.get_("C")
assert section_a_c == ["item1", "item2"]
```

!!!tip

    `Config`的`config`属性是该对象的数据源，是一个字典

---

关于`Config`的细节可以查看源码了解。需要注意的是，**程序运行期间，只会读取一次**`botoy.json`
