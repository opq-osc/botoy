class BotoyError(BaseException):
    pass


class ThreadPoolError(BotoyError):
    """线程池任务错误"""


class InvalidContextError(BotoyError):
    """不是正确的消息上下文对象"""


class InvalidConfigError(BotoyError):
    """配置文件有毛病"""


class InvalidPluginError(BotoyError):
    """插件问题"""
