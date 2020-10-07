"""辅助构建发送消息宏"""
import random
from collections.abc import Sequence
from typing import List, Union


def atUser(users: Union[List[int], int]) -> str:
    """艾特(ATUSER)
    :param users: 需要艾特的QQ号，如需多个请传列表
    """
    if not isinstance(users, Sequence):
        users = [users]
    return '[ATUSER(%s)]' % ','.join([str(i) for i in users])


def picFlag() -> str:
    """改变图片顺序"""
    return '[PICFLAG]'


def showPic(code: int = None) -> str:
    """秀图宏
    :param code: 秀图样式编号 40000-40006, 如不传则随机选取一个
            40000 秀图  40001 幻影  40002 抖动
            40003 生日  40004 爱你  40005 征友
            40006 无(只显示大图无特效)
    """
    if code is None:
        code = random.randint(40000, 40007)
    return '[秀图%d]' % code


def getUserNick(user: int) -> str:
    """获取用户昵称"""
    return '[GETUSERNICK(%d)]' % user
