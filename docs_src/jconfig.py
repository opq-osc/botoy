from botoy import jconfig


"""直接获取数据

json数据就是字典，jconfig支持运算符[]，属性，get方法获取数据
"""

assert jconfig.host == jconfig['host'] == jconfig.get('host') == 'http://127.0.0.1'

"""
上面三种方式获取的结果基本相同，和原生字典不同的是如果配置不存在时都不会报错，而是返回 None
其中 get 方法第二个参数可以指定默认值
"""


"""获取配置块，然后获取配置

对所有数据都用第一种直接获取的方式，当然可以
"""

token = jconfig['github.token']  # github token
username = jconfig['github.username']  # github username
issue_format = jconfig['github.issue.format']  # github issue format
issue_includeUrl = jconfig['github.issue.includeUrl']  # False
pr_format = jconfig['github.pr.format']  # github pr format
pr_includeUrl = jconfig['github.pr.includeUrl']  # True

"""
这样明显过于冗长，如果配置更多点，就更加麻烦了，
我们可以用类似命名空间的方式分成几个配置块(Configuration)
"""

github = jconfig.get_configuration('github')

token = github.get('token')  # github token
username = github[str].get('username')  # github token
issue_format = github.get('issue.format')  # github issue format
pr_includeUrl = github.get('pr.includeUrl')  # True

"""当然也可以这样"""
issue = jconfig.get_configuration('github.issue')
issue_format = issue.get('format')  # github issue format
issue_includeUrl = issue[bool].get('includeUrl')  # False
""""""

"""
jconfig.get_configuration方法 和其返回的Configuration的get方法，第一个参数均可以使用
点命名，前者参数名式section，后者是key，对应原数据键名为section+key

另外你还会发现在get方法之前还对Configuration使用了[]运算符，这是一个类型注解的小工具，是可选的！
如果你需要对获取的值做进一步处理，为了获取补全提示，就使用
"""

"""
你现在可能觉得一般，代码反而变多了, 是的光获取确实没什么变化

下面来介绍Configuration的其他方法
"""

issue = jconfig.get_configuration('github.issue')

"""has 判断是否存在配置
"""

# 是否存在github.issue.format
print(issue.has('format'))

"""update 更新(修改)配置
"""

# 修改github.issue.includeUrl
issue.update('includeUrl', True)
# 删除github.issue.format
issue.update('format', ...)  # https://docs.python.org/3/library/constants.html#Ellipsis

"""
update方法会修改botoy.json的数据。需要注意的是，此时Configuration的数据并没有更新
要使用最新数据，则需要重新获取(jconfig.get_configuration)
"""

"""提示
jconfig.get_configuration 的参数可以None，不传则表示全局配置块

比如可以这样修改数据
"""

config = jconfig.get_configuration()
config.update('host', 'new host')
config.update('github.pr.format', 'new github pr format')
