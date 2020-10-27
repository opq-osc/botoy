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
