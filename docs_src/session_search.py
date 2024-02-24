"""发送 查询 即可进入查询模式"""

from botoy.decorators import equal_content, ignore_botself
from botoy.session import SessionHandler, ctx, session


def search(word):
    return f"查询到关于【{word}】的内容如下..."


search_handler = SessionHandler(
    ignore_botself,
    equal_content("查询"),
    single_user=True,
    expiration=1 * 60,
).receive_group_msg()


@search_handler.handle
def _():
    session.send_text("查询模式开启，发送任意消息即可查询，发送`退出`即可退出查询模式")
    while True:
        word = session.pop("word", wait=True)
        if word == "退出":
            session.send_text("好哒~")
            search_handler.finish()
        session.send_text(search(word))
