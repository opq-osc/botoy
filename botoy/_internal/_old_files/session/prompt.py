from typing import List


class Prompt:
    def __init__(self, method, *args, **kwargs):
        self.method = method
        self.args = args
        self.kwargs = kwargs

    @classmethod
    def friend_picture(
        cls, url: str = "", base64: str = "", md5s: List[str] = [], text: str = ""
    ) -> "Prompt":
        return cls(
            "sendFriendPic",
            user="[user]",
            picUrl=url,
            picBase64Buf=base64,
            picMd5s=md5s,
            content=text,
        )

    @classmethod
    def group_picture(
        cls, url: str = "", base64: str = "", md5s: List[str] = [], text: str = ""
    ) -> "Prompt":
        return cls(
            "sendGroupPic",
            group="[group]",
            picUrl=url,
            picBase64Buf=base64,
            picMd5s=md5s,
            content=text,
        )
