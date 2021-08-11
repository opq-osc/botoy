# pylint: disable=W0613
def equal_content(string: str):
    """发送的内容与指定字符串相等时 GroupMsg, FriendMsg"""


def in_content(string: str, raw: bool = True):
    """Content字段包括指定字符串  GroupMsg, FriendMsg

    :param string: 需要包含的字符串, 支持使用正则查找
    :param raw: 为True则使用最原始的Content字段数据进行查找, 即图片这类消息会包含图片链接、
                图片MD5之类的数据; 为False则会提取真正发送的文字部分内容
    """


def from_these_groups(*groups):
    """只接受这些群组的消息 GroupMsg"""


def from_these_users(*users):
    """仅接受来自这些用户的消息 GroupMsg, FriendMsg"""


def ignore_botself(func=None):
    """忽略机器人自身的消息 GroupMsg, FriendMsg"""


def ignore_these_groups(*groups):
    """不接受这些群组的消息 GroupMsg"""


def ignore_these_users(*users):
    """忽略这些人的消息 GroupMsg, FriendMsg"""


def from_botself(func=None):
    """只处理机器人自身的消息 GroupMsg, FriendMsg"""


def startswith(string: str):
    """Content以指定前缀开头  GroupMsg, FriendMsg
    :param string: 前缀字符串, 会解析图片消息的Content
    """


def these_msgtypes(*msgtypes):
    """仅接受该些类型消息  GroupMsg, FriendMsg
    模块collection中定义了这些消息类型
    """


def with_pattern(pattern: str):
    """正则匹配Content字段 GroupMsg, FriendMsg
    因为使用这种功能一般匹配的内容都比较特殊,像图片，视频之类的消息基本是不会符合匹配条件的,
    所以不会解析特殊的消息, 均采用最原始的Content字段进行匹配,

    注意: 成功匹配才会执行该接收函数,匹配到的结果是一个列表,该结果会增加为ctx的``_pattern_result``属性

    :param pattern: 需要进行匹配的``正则表达式字符串``
    """


def ensure_tempMsg(func=None):
    """只接收私聊信息 FriendMsg"""


def from_phone(func=None):
    """来自手机的消息(给自己发的) FriendMsg"""


def from_admin(func=None):
    """来自群管理员(列表包括群主)的消息 GroupMsg
    管理员列表会进行``缓存``，调用520次后再次刷新, 所以可以放心使用"""


def queued_up(func=None, *, name="default"):
    """队列执行函数
    :param name: 指定队列分组, 不同的名称用不同的队列
    """


def ignore_tempMsg(func=None):
    """忽略私聊信息 FriendMsg"""


def on_regexp(pattern: Union[str, re.Pattern]):
    """正则匹配Content字段 GroupMsg, FriendMsg
    因为使用这种功能一般匹配的内容都比较特殊,像图片，视频之类的消息基本是不会符合匹配条件的,
    所以不会解析特殊的消息, 均采用最原始的Content字段进行匹配,

    匹配使用的是`re.match`方法，匹配结果可通过`ctx._match`属性调用

    :param pattern: 正则表达式
    """


def common_text(
    func=None,
    equal: str = None,
    in_: str = None,
    starts: str = None,
    ends: str = None,
    user: Union[int, List[int]] = None,
    group: Union[int, List[int]] = None,
    ignore_user: Union[int, List[int]] = None,
    ignore_group: Union[int, List[int]] = None,
    ignore_bot=True,
):
    """常见对文字消息的处理(不考虑私聊消息) GroupMsg,FriendMsg
    :param equal: 内容需要相等(==)
    :param in_: 内容需要包含，该项支持正则表达式(re.findall)
    :param starts: 内容以该项开头(startswith)
    :param ends: 内容以该项结尾(endswith)
    :param user: 来自该用户(们)(in)
    :param group: 来自该群组(们)(in)
    :param ignore_user: 忽略该用户(们)(not in)
    :param ignore_group: 忽略该群组(们)(not in)
    :param ignore_bot: 忽略机器人自身
    """


def need_action(func=None):
    """自动创建action并作为接收函数第2个参数传入
    你需要修改接收函数, 并且该装饰器只能放在最后（下）面!
    """
