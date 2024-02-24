"""test plugin_receiver"""

import time

from botoy import S
from botoy.contrib import plugin_receiver
from botoy.decorators import equal_content, ignore_botself


def a(t):
    count = 0

    def b():
        nonlocal count
        count += 1
        n = count

        @ignore_botself
        @equal_content("test plugin_receiver")
        def c(_):
            S.text(f"{t}_{n}")
            time.sleep(1)

        return c

    return b


group = a("group")

for _ in range(5):
    plugin_receiver.group(group())
