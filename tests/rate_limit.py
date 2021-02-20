import os
import threading
import time
import unittest

from botoy import Botoy, Action


class BotoyTest(unittest.TestCase):
    uin = os.environ.get('IOT_QQ', 123456789)
    host = os.environ.get('IOT_HOST', 'http://127.0.0.1')
    port = os.environ.get('IOT_PORT', 8888)

    def test_rate_limit(self):
        action = Action(qq=self.uin, host=self.host, port=self.port)
        requests = ['getUserList', 'getGroupList']

        def send(func: str):
            c = getattr(action, func)
            c()

        i = 0
        while i <= 5:
            threading.Thread(target=send, args=[requests[i % 2]]).start()
            i += 1


if __name__ == '__main__':
    unittest.main()
