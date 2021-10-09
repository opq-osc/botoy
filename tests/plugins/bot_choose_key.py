"""test choose key"""

from botoy.decorators import equal_content
from botoy.session import SessionHandler, session

handler = SessionHandler(equal_content("test choose key")).receive_group_msg()


@handler.handle
def _():
    items = [
        {"name": "python", "value": "py"},
        {"name": "golang", "value": "go"},
        {"name": "java", "value": "java"},
        {"name": "javascript", "value": "js"},
    ]
    if ret := session.choose(items, key=lambda x: x["name"]):
        item, _ = ret
        session.send_text(item["value"])

    handler.finish()
