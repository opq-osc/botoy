from botoy.contrib import RateLimit

# 2分钟只能调用5次
limit = RateLimit(calls=5, period=2 * 60)


# 方式一：以装饰器方式直接代理调用行为


@limit
def func():
    """这个函数在2分钟内只能调用5次，在限制时间内，调用会被忽略"""


# 方式二：手动处理控制逻辑
def work_func(from_user, content):
    # 有其他的情况不限制调用次数，比如是管理员调用
    if from_user == "admin":
        # 如果管理员发送重新计算的指令
        if content == "重置":
            limit.reset()
        print("admin is doing something")
    else:
        # 其他情况
        # 如果已经限制，则不做任何事
        # 如果未被限制，则做事，并且记录下来
        if limit.permitted():
            print("do someing...")
            limit.add(1)
