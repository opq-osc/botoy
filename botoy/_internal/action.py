import asyncio
import base64 as _base64
import re
from typing import Any, List, Optional, Tuple, TypeVar, Union
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from .utils import get_image_size

T = TypeVar("T")

from .config import jconfig
from .context import GroupMsg
from .log import logger


class BaseResponse(BaseModel):
    Ret: int = 0
    ErrMsg: str = ""


class Response(BaseModel):
    CgiBaseResponse: BaseResponse
    ResponseData: Any


lock = asyncio.Lock()


def get_base_url(url):
    if not re.match(r"^(http|https|ws)://", url):
        url = "http://" + url
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    assert hostname, f"{url} 有误，请检查!"
    port = parsed_url.port
    return f"http://{hostname}{ ':'+ str(port) if port is not None else ''}"


def to_list(item: Union[T, List[T]]) -> List[T]:
    if isinstance(item, List):
        return item
    return [item]


def add_image(
    images: list, resp: "Action.UploadResponse", size: Optional[Tuple[int, int]] = None
):
    item = {
        "FileMd5": resp.FileMd5,
        "FileSize": resp.FileSize,
        "FileId": resp.FileId,
    }
    if size:
        item["Height"] = size[0]
        item["Width"] = size[1]
    images.append(item)


class Action:
    def __init__(
        self,
        qq: Optional[int] = None,
        url: Optional[str] = None,
        timeout: int = 20,
    ):
        self.base_url = get_base_url(url or jconfig.url)
        self._qq = int(qq or jconfig.qq or 0)

        self.c = httpx.AsyncClient(
            headers={"Content-Type": "application/json"},
            timeout=timeout + 5,
            base_url=self.base_url,
            params={"timeout": timeout},
        )

    @property
    async def qq(self) -> int:
        if self._qq == 0:
            self._qq = (await self.getAllBots())[0]
        return int(self._qq)

    def set_url(self, url):
        self.base_url = get_base_url(url)
        self.c.base_url = self.base_url

    def set_qq(self, qq: int):
        self._qq = qq

    async def close(self):
        return await self.c.aclose()

    #
    async def __aenter__(self):
        return self

    #
    async def __aexit__(self, *args):
        return await self.c.__aexit__(*args)

    def build_request(self, request, cmd="MessageSvc.PbSendMsg") -> dict:
        return {"CgiCmd": cmd, "CgiRequest": request}

    ############发送相关############

    class SendFriendTextResponse(BaseModel):
        MsgTime: int
        MsgSeq: int

    async def sendFriendText(self, user: int, text: str):
        """发送好友文本消息"""
        data = await self.post(
            self.build_request({"ToUin": user, "ToType": 1, "Content": text})
        )
        return self.SendFriendTextResponse.parse_obj(data)

    async def sendPrivateText(self, user: int, group: int, text: str):
        """发送私聊文本消息"""
        data = await self.post(
            self.build_request(
                {"ToUin": user, "GroupCode": group, "ToType": 3, "Content": text}
            )
        )
        return self.SendFriendTextResponse.parse_obj(data)

    async def sendFriendPic(
        self,
        user: int,
        *,
        text: str = "",
        url: Union[str, List[str]] = "",
        base64: Union[str, List[str]] = "",
        # md5: Union[str, List[str]] = '',
    ):
        """发送好友图片消息
        :param user: 好友ID
        :param text: 发送文字内容
        :param url: 发送图片链接, 可以使用列表发送多张图片
        :param base64: 发送图片base64, 可以使用列表发送多张图片
        """
        # :param md5: 发送图片md5或md5列表, 可以为列表
        req = {
            "ToUin": user,
            "ToType": 1,
            "Content": text,
        }
        # images
        url_list = [url for url in to_list(url) if url]
        base64_list = [b64 for b64 in to_list(base64) if b64]
        # md5_list = [md5 for md5 in to_list(md5) if md5]

        images = []

        for url in url_list:
            size = None
            try:
                res = await self.c.get(
                    url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
                )
                res.raise_for_status()
            except Exception:
                pass
            else:
                size = get_image_size(res.content)
            add_image(images, await self.upload(1, url=url), size)
            await asyncio.sleep(0.5)
        for b64 in base64_list:
            size = get_image_size(_base64.b64decode(b64))
            add_image(images, await self.upload(1, base64=b64), size)
            await asyncio.sleep(0.5)
        # for md5 in md5_list:
        #     images.append({'FileMd5': md5})
        req["Images"] = images
        ###########

        data = await self.post(self.build_request(req))
        return self.SendGroupPicResponse.parse_obj(data)

    class SendFriendVoiceResponse(BaseModel):
        MsgTime: int
        MsgSeq: int

    async def sendFriendVoice(self, user: int, *, url: str = "", base64: str = ""):
        """发送好友语音消息
        :param url: 语音网络链接
        :param base64: 语音文件base64编码
        """
        assert any([url, base64]), "缺少参数"
        if url:
            file = await self.upload(26, url=url)
        else:
            file = await self.upload(26, base64=base64)
        data = await self.post(
            self.build_request(
                {
                    "ToUin": user,
                    "ToType": 1,
                    "Voice": {
                        "FileMd5": file.FileMd5,
                        "FileSize": file.FileSize,
                        "FileToken": file.FileToken,
                    },
                }
            )
        )
        return self.SendFriendVoiceResponse.parse_obj(data)

    #
    #     async def sendFriendXml(self, user: int, content: str) -> dict:
    #         """发送好友Xml消息"""
    #         return await self.post(
    #             "SendMsgV2",
    #             {
    #                 "ToUserUid": user,
    #                 "SendToType": 1,
    #                 "SendMsgType": "XmlMsg",
    #                 "Content": content,
    #             },
    #         )
    #
    #     async def sendFriendTeXiaoText(self, user: int, text: str) -> dict:
    #         """发送好友特效文本消息"""
    #         return await self.post(
    #             "SendMsgV2",
    #             {
    #                 "ToUserUid": user,
    #                 "SendToType": 1,
    #                 "SendMsgType": "TeXiaoTextMsg",
    #                 "Content": text,
    #             },
    #         )
    #

    class SendGroupTextResponse(BaseModel):
        MsgTime: int
        MsgSeq: int

    async def sendGroupText(
        self,
        group: int,
        text: str,
        atUser: Union[int, List[int]] = 0,
        atUserNick: Union[str, List[str]] = "",
    ):
        """发送群组文本消息
        :param group: 发送群ID
        :param content: 发送内容
        :param atUser: 需要艾特的用户QQ号
        :param atUserNick: 需要艾特的用户昵称, 需与atUser对应，如果缺失会将被艾特用户QQ号作为昵称
        """
        # NOTE: 用两个参数是因为，后续可能会支持不提供nick也能正确艾特出来
        # 因为个人觉得还需要传nick太多余了，但目前不传不行
        if isinstance(atUser, int) and atUser != 0:
            at_uins = [atUser]
        elif isinstance(atUser, List):
            at_uins = atUser
        else:
            at_uins = []

        if isinstance(atUserNick, str) and atUserNick:
            at_nicks = [atUserNick]
        elif isinstance(atUserNick, List):
            at_nicks = atUserNick
        else:
            at_nicks = []

        at_list = []
        for idx, uin in enumerate(at_uins):
            try:
                nick = at_nicks[idx]
            except:
                nick = str(uin)
            at_list.append({"Uin": uin, "Nick": nick})

        data = await self.post(
            self.build_request(
                {
                    "ToUin": group,
                    "ToType": 2,
                    "Content": text,
                    "AtUinLists": at_list,
                }
            )
        )
        return self.SendGroupTextResponse.parse_obj(data)

    async def at(self, group: int, user: Union[int, List[int]]):
        """仅@群成员"""
        return await self.sendGroupText(group, text=" ", atUser=user)

    class UploadResponse(BaseModel):
        FileMd5: str
        FileSize: int
        FileId: Optional[int]
        FileToken: Optional[str]

    async def upload(self, cmd: int, url: str = "", base64: str = "", path: str = ""):
        """上传资源文件
        :param cmd: 1好友图片 2群组图片 26好友语音 29群组语音
        :param url: 链接
        :param base64: base64
        :param path: 文件路径，和机器人服务端在同一个文件系统中

        url、base64和path三项不能同时存在

        {
            "CgiBaseResponse": {
                "Ret": 0,
                "ErrMsg": "string"
            },
            "ResponseData": {
                "FileMd5": "string",
                "FileSize": 0,
                "FileToken": "string"
            },
            "Data": null
        }
        """
        req = {"CommandId": cmd}
        if url:
            req["FileUrl"] = url  # type: ignore
        elif base64:
            req["Base64Buf"] = base64  # type: ignore
        elif path:
            req["FilePath"] = path  # type: ignore
        else:
            raise ValueError("缺少参数")
        data = await self.post(
            self.build_request(req, "PicUp.DataUp"),
            path="/v1/upload",
            funcname="",
            timeout=60,  # 这个timeout可能不能写死
        )
        return self.UploadResponse.parse_obj(data)

    class SendGroupPicResponse(BaseModel):
        MsgTime: int
        MsgSeq: int

    async def sendPrivatePic(
        self,
        user: int,
        group: int,
        *,
        text: str = "",
        url: Union[str, List[str]] = "",
        base64: Union[str, List[str]] = "",
        # md5: Union[str, List[str]] = '',
    ):
        """发送私聊图片消息
        :param user: 好友ID
        :param group: 群号
        :param text: 发送文字内容
        :param url: 发送图片链接, 可以使用列表发送多张图片
        :param base64: 发送图片base64, 可以使用列表发送多张图片
        """
        # :param md5: 发送图片md5或md5列表
        req = {
            "ToUin": user,
            "GroupCode": group,
            "ToType": 3,
            "Content": text,
        }
        # images
        url_list = [url for url in to_list(url) if url]
        base64_list = [b64 for b64 in to_list(base64) if b64]
        # md5_list = [md5 for md5 in to_list(md5) if md5]

        images = []

        for url in url_list:
            size = None
            try:
                res = await self.c.get(
                    url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
                )
                res.raise_for_status()
            except Exception:
                pass
            else:
                size = get_image_size(res.content)
            add_image(images, await self.upload(1, url=url), size)
            await asyncio.sleep(0.5)
        for b64 in base64_list:
            size = get_image_size(_base64.b64decode(b64))
            add_image(images, await self.upload(1, base64=b64), size)
            await asyncio.sleep(0.5)
        # for md5 in md5_list:
        #     images.append({'FileMd5': md5})
        req["Images"] = images
        ###########

        data = await self.post(self.build_request(req))
        return self.SendGroupPicResponse.parse_obj(data)

    async def sendGroupPic(
        self,
        group: int,
        *,
        text: str = "",
        url: Union[str, List[str]] = "",
        base64: Union[str, List[str]] = "",
        # md5: Union[str, List[str]] = '',
        atUser: Union[int, List[int]] = 0,
        atUserNick: Union[str, List[str]] = "",
    ):
        """发送群组图片消息
        :param group: 发送群ID
        :param text: 发送文字内容
        :param url: 发送图片链接, 可以为列表
        :param base64: 发送图片base64, 可以为列表
        :param atUser: 需要艾特的用户QQ号, 可以为列表
        :param atUserNick: 需要艾特的用户昵称, 需与atUser对应，如果缺失会将被艾特用户QQ号作为昵称
        """
        # :param md5: 发送图片md5, 可以为列表
        req = {
            "ToUin": group,
            "ToType": 2,
            "Content": text,
        }
        # images
        url_list = [url for url in to_list(url) if url]
        base64_list = [b64 for b64 in to_list(base64) if b64]
        # FIXME: 支持用户直接传递md5，size，id
        # md5_list = [md5 for md5 in to_list(md5) if md5]

        images = []

        for url in url_list:
            size = None
            try:
                res = await self.c.get(
                    url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
                )
                res.raise_for_status()
            except Exception:
                pass
            else:
                size = get_image_size(res.content)
            imageUrl = await self.upload(2, url=url)
            add_image(images, imageUrl, size)
            await asyncio.sleep(0.5)
        for b64 in base64_list:
            size = get_image_size(_base64.b64decode(b64))
            add_image(images, await self.upload(2, base64=b64), size)
            await asyncio.sleep(0.5)
        # for md5 in md5_list:
        #     images.append({'FileMd5': md5})
        req["Images"] = images  # type: ignore
        ###########

        # at list
        at_uins = to_list(atUser) if atUser else []
        at_nicks = to_list(atUserNick) if atUserNick else []

        at_list = []
        for idx, uin in enumerate(at_uins):
            try:
                nick = at_nicks[idx]
            except:
                nick = str(uin)
            at_list.append({"Uin": uin, "Nick": nick})
        req["AtUinLists"] = at_list  # type: ignore
        ###########
        data = await self.post(self.build_request(req))
        return self.SendGroupPicResponse.parse_obj(data)

    class SendGroupVoiceResponse(BaseModel):
        MsgTime: int
        MsgSeq: int

    async def sendGroupVoice(self, group: int, *, url: str = "", base64: str = ""):
        """发送群组语音消息
        :param url: 语音网络链接
        :param base64: 语音文件base64编码
        """
        assert any([url, base64]), "缺少参数"
        if url:
            file = await self.upload(29, url=url)
        else:
            file = await self.upload(29, base64=base64)
        data = await self.post(
            self.build_request(
                {
                    "ToUin": group,
                    "ToType": 2,
                    "Voice": {
                        "FileMd5": file.FileMd5,
                        "FileSize": file.FileSize,
                        "FileToken": file.FileToken,
                    },
                }
            )
        )
        return self.SendGroupVoiceResponse.parse_obj(data)

    class SendGroupXmlResponse(BaseModel):
        MsgTime: int

    async def sendGroupXml(self, group: int, content: str):
        """发送群组Xml消息"""
        data = await self.post(
            self.build_request(
                {"ToUin": group, "ToType": 2, "SubMsgType": 12, "Content": content}
            )
        )
        return self.SendGroupXmlResponse.parse_obj(data)

    async def sendGroupJson(self, group: int, content: str):
        """发送群组Json消息"""
        data = await self.post(
            self.build_request(
                {"ToUin": group, "ToType": 2, "SubMsgType": 51, "Content": content}
            )
        )
        return self.SendGroupXmlResponse.parse_obj(data)

    #
    #     async def sendGroupTeXiaoText(self, group: int, text: str) -> dict:
    #         """发送群组特效文本消息"""
    #         return await self.post(
    #             "SendMsgV2",
    #             {
    #                 "ToUserUid": group,
    #                 "SendToType": 2,
    #                 "SendMsgType": "TeXiaoTextMsg",
    #                 "Content": text,
    #             },
    #         )
    #
    #     async def sendPrivateText(self, user: int, group: int, content: str) -> dict:
    #         """发送私聊文本消息"""
    #         return await self.post(
    #             "SendMsgV2",
    #             {
    #                 "ToUserUid": user,
    #                 "GroupID": group,
    #                 "SendToType": 3,
    #                 "SendMsgType": "TextMsg",
    #                 "Content": content,
    #             },
    #         )
    #
    #     async def sendPrivateXml(self, user: int, group: int, content: str) -> dict:
    #         """发送私聊Xml消息"""
    #         return await self.post(
    #             "SendMsgV2",
    #             {
    #                 "ToUserUid": user,
    #                 "GroupID": group,
    #                 "SendToType": 3,
    #                 "SendMsgType": "XmlMsg",
    #                 "Content": content,
    #             },
    #         )
    #
    #     async def sendPrivateVoice(
    #         self, user: int, group: int, *, voiceUrl: str = "", voiceBase64Buf: str = ""
    #     ) -> dict:
    #         assert any([voiceUrl, voiceBase64Buf]), "缺少参数"
    #         return await self.post(
    #             "SendMsg",
    #             {
    #                 "toUser": user,
    #                 "sendToType": 3,
    #                 "sendMsgType": "VoiceMsg",
    #                 "content": "",
    #                 "groupid": group,
    #                 "voiceUrl": voiceUrl,
    #                 "voiceBase64Buf": voiceBase64Buf,
    #             },
    #         )
    #
    #     async def sendPrivatePic(
    #         self,
    #         user: int,
    #         group: int,
    #         content: str = "",
    #         *,
    #         picUrl: str = "",
    #         picBase64Buf: str = "",
    #         picMd5s: Optional[Union[str, List[str]]] = None,
    #     ) -> dict:
    #         """发送私聊图片消息"""
    #         assert any([picUrl, picBase64Buf, picMd5s]), "缺少参数"
    #         if isinstance(picMd5s, str):
    #             picMd5s = [picMd5s]
    #         picMd5s = [  # type: ignore
    #             {"FileId": 1, "PicMd5": picmd5, "PicSize": 1} for picmd5 in picMd5s or []
    #         ]
    #         return await self.post(
    #             "SendMsgV2",
    #             {
    #                 "ToUserUid": user,
    #                 "GroupID": group,
    #                 "SendToType": 3,
    #                 "SendMsgType": "PicMsg",
    #                 "Content": content,
    #                 "PicUrl": picUrl,
    #                 "PicBase64Buf": picBase64Buf,
    #                 "PicMd5s": picMd5s,
    #             },
    #         )
    #
    async def sendPhoneText(self, content: str):
        """给手机发文字
        TODO: 目前并不是给手机发送消息，是给自己发送消息
        """
        return await self.sendFriendText(await self.qq, content)

    class ReplyGroupMsgResponse(BaseModel):
        MsgSeq: int
        MsgTime: int

    async def replyGroupMsg(
        self,
        target: GroupMsg,
        content: str,
        atUser: Union[int, List[int]] = 0,
        atUserNick: Union[str, List[str]] = "",
    ):
        """回复群消息"""
        req = {
            "ToUin": target.from_group,
            "ToType": 2,
            "ReplyTo": {
                "MsgSeq": target.msg_seq,
                "MsgTime": target.msg_time,
                "MsgUin": target.msg_uid,
            },
            "Content": content,
        }
        # at list
        at_uins = to_list(atUser) if atUser else []
        at_nicks = to_list(atUserNick) if atUserNick else []

        at_list = []
        for idx, uin in enumerate(at_uins):
            try:
                nick = at_nicks[idx]
            except:
                nick = str(uin)
            at_list.append({"Uin": uin, "Nick": nick})
        req["AtUinLists"] = at_list  # type: ignore
        data = await self.post(self.build_request(req))
        return self.ReplyGroupMsgResponse.parse_obj(data)

    #
    #     async def replyFriendMsg(
    #         self,
    #         user: int,
    #         content: str,
    #         msgSeq: int,
    #         msgTime: Optional[int] = None,
    #         rawContent: str = "",
    #     ):
    #         """发送回复消息, 回复好友消息
    #         下面的原消息表示需要回复的消息
    #         :param user: 原消息发送人
    #         :param content: 回复内容
    #         :param msgSeq: 原消息的msgSeq, 点击跳转到该条消息位置
    #         :param msgTime: 原消息的msgTime, 如果不指定，默认为当前时间戳
    #         :param rawContent: 原消息内容，可以任意指定，默认为空
    #         """
    #         return await self.post(
    #             "SendMsg",
    #             {
    #                 "toUser": user,
    #                 "sendToType": 1,
    #                 "sendMsgType": "ReplayMsg",
    #                 "content": content,
    #                 "replayInfo": {
    #                     "MsgSeq": msgSeq,
    #                     "MsgTime": msgTime or int(time.time()),
    #                     "UserID": user,
    #                     "RawContent": rawContent,
    #                 },
    #             },
    #         )
    #
    #     async def poke(self, user: int, group=0):
    #         """戳一戳，未设置群ID就是戳好友"""
    #         payload = {"UserID": user, "GroupID": group}
    #         if group == 0:
    #             payload["Type"] = 0
    #         else:
    #             payload["Type"] = 1
    #         return await self.post("OidbSvc.0xed3_1", payload)
    #
    #     async def repostVideo2Group(self, group: int, forwordBuf: str) -> dict:
    #         """转发视频到群聊
    #         :param group: 群号
    #         :param forwordBuf: 原视频的forwordBuf字段
    #         """
    #         return await self.post(
    #             "SendMsg",
    #             {
    #                 "toUser": group,
    #                 "sendToType": 2,
    #                 "sendMsgType": "ForwordMsg",
    #                 "forwordBuf": forwordBuf,
    #                 "forwordField": 19,
    #             },
    #         )
    #
    #     async def getVideoURL(self, group: int, videoMD5: str, videoURL: str) -> dict:
    #         """获取视频链接
    #         :param group: 群号
    #         :param videoMD5: 视频的 MD5 值，可以从上报的消息中获得
    #         :param videoURL: 上报的消息中传给的 url 值
    #         """
    #         return await self.post(
    #             "PttCenterSvr.ShortVideoDownReq",
    #             {"GroupID": group, "VideoUrl": videoURL, "VideoMd5": videoMD5},
    #         )
    #
    #     async def getFriendFileURL(self, fileID: str) -> dict:
    #         """获取好友文件链接
    #         :param fileID: 文件 ID，可由上报的消息中获得
    #         """
    #         return await self.post(
    #             "OfflineFilleHandleSvr.pb_ftn_CMD_REQ_APPLY_DOWNLOAD-1200",
    #             {"FileID": fileID},
    #         )
    #
    #     async def getGroupFileURL(self, group: int, fileID: str) -> dict:
    #         """获取好友文件链接
    #         :param group: 群号
    #         :param fileID: 文件 ID，可由上报的消息中获得
    #         """
    #         return await self.post(
    #             "OidbSvc.0x6d6_2",
    #             {"GroupID": group, "FileID": fileID},
    #         )
    #
    #     async def repostVideo2Friend(self, user: int, forwordBuf: str) -> dict:
    #         """转发视频到好友
    #         :param user: 好友QQ
    #         :param forwordBuf: 原视频的forwordBuf字段
    #         """
    #         return await self.post(
    #             "SendMsg",
    #             {
    #                 "toUser": user,
    #                 "sendToType": 1,
    #                 "sendMsgType": "ForwordMsg",
    #                 "forwordBuf": forwordBuf,
    #                 "forwordField": 19,
    #             },
    #         )
    #
    #     async def groupJoinAuth(self, ctx: EventMsg, cmd=None):
    #         """
    #         :param ctx: 事件EventMsg, 类型不匹配将报错
    #         :param cmd: True:同意进群,False:拒绝,None:忽略
    #         """
    #         join_group_info = eventParser.group_adminsysnotify(ctx)
    #         assert join_group_info, "事件类型不匹配"
    #         return await self.post(
    #             "AnswerInviteGroup",
    #             {
    #                 "Seq": join_group_info.Seq,
    #                 "Who": join_group_info.Who,
    #                 "Flag_7": join_group_info.Flag_7,
    #                 "Flag_8": join_group_info.Flag_8,
    #                 "GroupId": join_group_info.GroupId,
    #                 "Action": {True: 11, False: 12, None: 14}[
    #                     cmd
    #                 ],  # 11 agree , 14 忽略 , 12/21 disagree
    #             },
    #         )
    #
    #     async def uploadGroupFile(
    #         self,
    #         group: int,
    #         fileURL: str = "",
    #         fileBase64: str = "",
    #         filePath: str = "",
    #         fileName: str = "",
    #         fileType: str = "",
    #         notify: bool = True,
    #     ) -> dict:
    #         """上传群文件
    #         :param group: 群号
    #         :param fileURL: 文件网络地址, 和fileBase64二选一
    #         :param fileBase64: 文件base64编码, 和fileURL二选一
    #         :param filePath: 文件路径，注意该路径要确保机器人服务端能够访问到，并且该项设置后，fileName和fileType参数将无效
    #         :param fileName: 文件名(需包含拓展名)，如果不传则随机生成并且如果是使用URL上传则会尝试自动推测文件类型
    #         :param fileType: 文件的后缀名，如果指定了，会自动加在文件名(fileName)后面, 如 .txt 或 txt
    #         :param notify: 是否通知
    #         """
    #         # 将filePath作最高优先级，因为通过路径上传，fileName字段无效
    #         if not filePath:
    #             if not fileName:
    #                 fileName = str(uuid.uuid4())
    #                 # guess extension by url
    #                 if fileURL:
    #                     try:
    #                         async with httpx.AsyncClient() as client:
    #                             async with client.stream("GET", fileURL, timeout=5) as resp:
    #                                 content_type = resp.headers["content-type"]
    #                                 extension = mimetypes.guess_extension(content_type)
    #                                 if extension is not None:
    #                                     fileName = fileName + extension
    #                     except Exception:
    #                         pass
    #             if fileType:
    #                 if fileType.startswith("."):
    #                     fileName = fileName + fileType
    #                 else:
    #                     fileName = fileName + "." + fileType
    #         payload = {
    #             "ToUserUid": group,
    #             "SendMsgType": "UploadGroupFile",
    #             "FileName": fileName,
    #             "Notify": notify,
    #         }
    #         if filePath:
    #             payload.update({"FilePath": filePath})
    #         elif fileURL:
    #             payload.update({"FileUrl": fileURL})
    #         elif fileBase64:
    #             payload.update({"FileBase64": fileBase64})
    #         else:
    #             raise Exception("fileURL, fileBase64, filePath 必须给定其中一个")
    #         return await self.post("SendMsgV2", payload)
    #
    #     async def openRedBag(self, redBagInfo: dict):
    #         """打开红包
    #
    #         :param redBagInfo: 红包信息, ctx.RedBaginfo
    #         """
    #         return await self.post("OpenRedBag", redBagInfo)
    #
    #     async def getCookies(self) -> dict:
    #         """获取QQ相关cookie"""
    #         return await self.get("GetUserCook")
    #
    #     async def getUserInfo(self, user: int) -> dict:
    #         """获取用户信息昵称头像等"""
    #         return await self.post("GetUserInfo", {"UserID": user})
    #
    #     async def getSummaryCard(self, user: int) -> dict:
    #         """获取企鹅卡片资料"""
    #         return await self.post("SummaryCard.ReqSummaryCard", {"UserID": user})
    #
    #     async def getUserList(self) -> List[dict]:
    #         """获取好友列表"""
    #         friend_list = []
    #         start_index = 0
    #         while True:
    #             data = await self.post("GetQQUserList", {"StartIndex": start_index})
    #             if "Friendlist" not in data:
    #                 break
    #             friend_list.extend(data["Friendlist"])
    #             if len(friend_list) >= int(data.get("Totoal_friend_count", 0)):  # 这里有个拼写错误
    #                 break
    #             if "GetfriendCount" not in data:
    #                 break
    #             start_index += int(
    #                 data.get("GetfriendCount", 999999)
    #             )  # 设置 999999 为了在 API 坏了的情况下能跳出循环
    #         return friend_list
    #
    #     async def getGroupList(self) -> List[dict]:
    #         """获取群列表"""
    #         next_token = ""
    #         group_list = []
    #         while True:
    #             data = await self.post("GetGroupList", {"NextToken": next_token})
    #             if "TroopList" not in data:
    #                 break
    #             group_list.extend(data["TroopList"])
    #             next_token = data.get("NextToken", "")
    #             if not next_token:
    #                 break
    #         return group_list
    #
    #     async def getGroupMembers(self, group: int) -> List[dict]:
    #         """获取群成员列表"""
    #         members = []
    #         lastUin = 0
    #         while True:
    #             data = await self.post(
    #                 "GetGroupUserList", {"GroupUin": group, "LastUin": lastUin}
    #             )
    #             if "MemberList" in data:
    #                 members.extend(data["MemberList"])
    #             if "LastUin" not in data or data["LastUin"] == 0:
    #                 break
    #             lastUin = data["LastUin"]
    #             time.sleep(0.6)
    #         return members
    #
    #     async def getGroupAdminList(self, group: int, include_owner=True) -> List[dict]:
    #         """获取群管理员列表
    #         :param group: 群号
    #         :param include_owner: 是否包括群主
    #         """
    #         members = await self.getGroupMembers(group)
    #         if include_owner:
    #             # 获取群主id
    #             owner = 0
    #             for groupInfo in await self.getGroupList():
    #                 if groupInfo["GroupId"] == group:
    #                     owner = groupInfo["GroupOwner"]
    #                     break
    #             admins = [
    #                 member
    #                 for member in members
    #                 if member["GroupAdmin"] == 1 or member["MemberUin"] == owner
    #             ]
    #         else:
    #             admins = [member for member in members if member["GroupAdmin"] == 1]
    #         return admins
    #
    async def getClusterInfo(self) -> dict:
        """获取当前集群信息"""
        return await self.get("", path="v1/clusterinfo", params={"isShow": 1, "qq": 1})  # type: ignore

    async def getQrCode(self, qq="", devicename="") -> str:
        """获取登录二维码base64
        :param qq: 复用设备信息登录需填写 首次登录会随机设备信息
        :param devicename: 登录的设备名称
        """
        resp = await self.get(
            "",
            path=f"/v1/login/getqrcode",
            params={"qq": qq, "devicename": devicename, "json": 1},
        )
        return resp["BQrpic"]  # type: ignore

    async def getGroupList(self) -> List[dict]:
        """获取群列表"""
        data = await self.post(self.build_request(request={}, cmd="GetGroupLists"))
        return data["GroupLists"]  # type: ignore

    async def getGroupMembers(self, group: int) -> List[dict]:
        """获取群成员列表"""
        members = []
        LastBuffer = ""
        while True:
            data = await self.post(
                self.build_request(
                    request={"Uin": group, "LastBuffer": LastBuffer},
                    cmd="GetGroupMemberLists",
                )
            )
            if "MemberLists" in data:  # type: ignore
                members.extend(data["MemberLists"])  # type: ignore
            if "LastBuffer" not in data or data["LastBuffer"] == "":  # type:ignore
                break
            LastBuffer = data["LastBuffer"]  # type: ignore
        return members

    async def getGroupAdminList(self, group: int, include_owner=True) -> List[dict]:
        """获取群管理员列表
        :param group: 群号
        :param include_owner: 是否包括群主
        """
        members = await self.getGroupMembers(group)
        if include_owner:
            admins = [member for member in members if member["MemberFlag"] in [1, 2]]
        else:
            admins = [member for member in members if member["MemberFlag"] == 2]
        return admins

    async def revokeGroupMsg(self, group: int, msgSeq: int, msgRandom: int):
        """撤回群消息
        :param group: 群号
        :param msgSeq: 消息msgSeq
        :param msgRandom: 消息msgRandom
        """
        return await self.post(
            self.build_request(
                request={"Uin": group, "MsgSeq": msgSeq, "MsgRandom": msgRandom},
                cmd="GroupRevokeMsg",
            )
        )

    async def revoke(self, msg: GroupMsg):
        """撤回群消息"""
        return await self.revokeGroupMsg(msg.from_group, msg.msg_seq, msg.msg_random)

        #
        #     async def setUniqueTitle(self, user: int, group: int, title: str):
        #         """设置群头衔"""
        #         return await self.post(
        #             "OidbSvc.0x8fc_2",
        #             {"GroupID": group, "UserID": user, "NewTitle": title},
        #         )
        #

    async def modifyGroupCard(self, user: str, group: int, nick: str):
        """修改用户群名片
        :param user: 用户uid，注意是str类型，格式为：u_
        :param group: 群号
        :param nick: 新群名片昵称
        """
        return await self.post(
            self.build_request(
                {"OpCode": 2300, "Uin": group, "Uid": user, "Nick": nick}
            )
        )

    async def shutUserUp(self, group: int, user_uid: str, ShutTime: int):
        """禁言用户
        :param group: 群id
        :param user_uid: 用户uid
        :param time: 禁言时间。单位秒 至少60秒 至多30天 参数为0解除禁言
        """
        req = {
            "OpCode": 4691,
            "Uin": group,
            "Uid": user_uid,
            "BanTime": ShutTime,
        }
        return await self.post(self.build_request(req, "SsoGroup.Op"))

        #
        #     async def shutAllUp(self, group: int, switch: int):
        #         """全体禁言
        #         :param switch: 1 开启; 0 关闭
        #         """
        #         return await self.post(
        #             "OidbSvc.0x89a_0",
        #             {"GroupID": group, "Switch": switch},
        #         )
        #
        #     async def setGroupAnnounce(
        #         self,
        #         group: int,
        #         text: str,
        #         pinned: bool = False,
        #         title: str = "",
        #         typ: bool = True,
        #     ):
        #         """设置群公告
        #         :param group: 群号
        #         :param text: 内容
        #         :param pinned: 是否置顶
        #         :param title: 标题,可以空
        #         :param typ: 是否发送新成员
        #         """
        #         return await self.post(
        #             path="/v1/Group/Announce",
        #             funcname="",
        #             payload={
        #                 "GroupID": group,
        #                 "Title": title,
        #                 "Text": text,
        #                 "Pinned": 1 if pinned else 0,
        #                 "Type": 20 if typ else 10,  # 20 发给新成员, 10 弹窗
        #             },
        #         )
        #
        #     async def likeUser(self, user: int, cmd=0) -> dict:
        #         """给某人点赞
        #         :param user: 用户QQ号
        #         :param cmd: 发送包选项, 0 或 1; 0表示使用``QQZan``; 1表示使用``OidbSvc.0x7e5_4``, 默认为0
        #         """
        #         return await self.post(
        #             "QQZan" if cmd == 0 else "OidbSvc.0x7e5_4", {"UserID": user}
        #         )
        #
        #     async def toggleGroupAdmin(self, user: int, group: int, flag=1) -> dict:
        #         """设置和取消群管理员
        #         :param user: 用户QQ
        #         :param group: 群号
        #         :param flag: 1 或 0, 1表示设置为管理员; 0 表示取消管理员, 默认为1
        #         """
        #         return await self.post(
        #             "OidbSvc.0x55c_1",
        #             {"GroupID": group, "UserID": user, "Flag": 0 if flag == 0 else 1},
        #         )
        #
        #
        #     async def inviteUserJoinGroup(self, group: int, user: int) -> dict:
        #         """拉人入群
        #         :param group: 哪个群?
        #         :param user: 拉谁?
        #         """
        #         return await self.post(
        #             "GroupMgr",
        #             {"ActionType": 8, "GroupID": group, "ActionUserID": user, "Content": ""},
        #         )
        #
        #     async def joinGroup(self, group: int, content: str = "") -> dict:
        #         """加入群聊
        #         :param group: 哪个群?
        #         :param content: 加群理由
        #         """
        #         return await self.post(
        #             "GroupMgr",
        #             {"ActionType": 1, "GroupID": group, "ActionUserID": 0, "Content": content},
        #         )
        #

    async def exitGroup(self, group: int):
        """退出群聊
        :param group: 哪个群?
        """
        return await self.post(
            self.build_request({"OpCode": 4247, "Uin": group}), "SsoGroup.Op"
        )

    async def driveUserAway(self, group: int, user_uid: str):
        """移出群聊
        :param group: 哪个群?
        :param user_uid: 把谁踢出去?
        """
        return await self.post(
            self.build_request({"OpCode": 2208, "Uin": group, "Uid": user_uid})
        )
        #
        #     async def refreshKeys(self) -> dict:
        #         """刷新key二次登陆"""
        #         return await self.get("", path="/v1/RefreshKeys")
        #
        #     async def dealFriend(self, ctx: EventMsg, cmd=None) -> dict:
        #         """处理好友请求
        #         :param ctx: 事件EventMsg, 类型不匹配将报错
        #         :param cmd: True:同意,False:拒绝,None:忽略
        #         """
        #         friend_add_info = eventParser.friend_add(ctx)
        #         assert friend_add_info, "事件类型不匹配"
        #         return await self.post(
        #             "DealFriend",
        #             {
        #                 "UserID": friend_add_info.UserID,
        #                 "FromType": friend_add_info.FromType,
        #                 "Type": friend_add_info.Type,
        #                 "Field_3": friend_add_info.Field_3,
        #                 "Field_8": friend_add_info.Field_8,
        #                 "Content": friend_add_info.Content,
        #                 "FromGroupId": friend_add_info.FromGroupId,
        #                 "FromGroupName": friend_add_info.FromGroupName,
        #                 "Action": {True: 2, False: 3, None: 1}[cmd],  # 1忽略2同意3拒绝
        #             },
        #         )
        #
        #     async def logout(self, flag=False) -> dict:
        #         """退出指定QQ
        #         :param flag: 是否删除设备信息文件
        #         """
        #         return await self.post("LogOut", {"Flag": flag})
        #
        #     async def getGroupPicInfo(self, url: str = "", base64: str = ""):
        #         """上传群图片获取图片信息
        #         :param url: 图片链接
        #         :param base64: 图片base64
        #         """
        #         assert any([url, base64]), "缺少参数"
        #         return await self.post(
        #             "", {"PicUrl": url, "PicBase64Buf": base64}, path="/v1/GetGroupPicInfo"
        #         )
        #
        #     async def updateAvatar(self, url: str):
        #         """上传头像
        #         :param url: 图片链接
        #         """
        #         return await self.post("", {"HDIMGUrl": url}, path="/v1/User/SelfHDIMG")
        #
        #     async def updateProfile(
        #         self,
        #         NickName: str,
        #         Age: int,
        #         Sex: int,
        #         ProviceID: int,
        #         CounrtyID: int,
        #         CityID: int,
        #         Flag: int = 0,
        #     ):
        #         """更改资料
        #         :param NickName: QQ名称
        #         :param Age: 年龄
        #         :param Sex: 性别 男1 女2
        #         :param ProviceID: 省份ID
        #         :param CounrtyID: 国家ID
        #         :param CityID: 城市ID
        #         :param Flag: 默认为0正常设置 为1则清空资料保留昵称
        #         """
        #         return await self.post(
        #             "",
        #             {
        #                 "NickName": NickName,
        #                 "Age": Age,
        #                 "Sex": Sex,
        #                 "ProviceID": ProviceID,
        #                 "CounrtyID": CounrtyID,
        #                 "CityID": CityID,
        #                 "Flag": Flag,
        #             },
        #             path="/v1/User/SelfProfile",
        #         )
        #

    async def getAllBots(self) -> List[int]:
        """获取OPQ登陆的所有机器人QQ号"""
        return [i["QQ"] for i in (await self.getClusterInfo())["QQUsers"]]

    class QueryUinByUidResponse(BaseModel):
        Uin: int
        Uid: str
        Nick: str
        Head: str
        Signature: str
        Sex: int
        Level: int

    async def queryUinByUid(self, uid: str):
        """用户Uid转Uin，返回值中不仅仅包含uin, 还包括用户信息
        :param uid: 用户uid
        """
        req = self.build_request({"Uid": uid}, "QueryUinByUid")
        data = await self.post(req)
        return self.QueryUinByUidResponse.parse_obj(
            data[0] if isinstance(data, list) else data
        )

    async def getClientKey(self) -> int:
        """自己看OPQ文档"""
        return await self.post(self.build_request({}, "GetClientKey"))

    class GetPSKeyResponse(BaseModel):
        Domain: str
        PSKey: str

    async def getPSKey(self, domain: str = "qzone.qq.com"):
        """自己看OPQ文档"""
        data = await self.post(self.build_request({"Domain": domain}, "GetPSKey"))
        return self.GetPSKeyResponse.parse_obj(data)

        ############################################################################

    async def baseRequest(
        self,
        method: str,
        funcname: str,
        path: str,
        payload: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: Optional[int] = None,
    ):
        """基础请求方法, 提供部分提示信息，出错返回空字典，其他返回服务端响应结果"""
        async with lock:
            await asyncio.sleep(0.5)

        params = params or {}
        params["funcname"] = funcname
        if "qq" not in params:
            params["qq"] = await self.qq

        ret = None
        try:
            resp = await self.c.request(
                method,
                httpx.URL(url=path, params=params),
                json=payload,
                timeout=timeout,
            )
            ret = resp.json()
            resp_model = Response.parse_obj(ret)
            if resp_model.CgiBaseResponse.ErrMsg:
                if resp_model.CgiBaseResponse.Ret == 0:
                    logger.success(resp_model.CgiBaseResponse.ErrMsg)
                else:
                    logger.error(resp_model.CgiBaseResponse.ErrMsg)
            return resp_model.ResponseData
        except Exception as e:
            logger.error(e)
            logger.debug(f"接口返回数据：{ret}")
            return None

    #
    async def post(
        self,
        payload: dict,
        funcname: str = "MagicCgiCmd",
        params: Optional[dict] = None,
        path: str = "/v1/LuaApiCaller",
        timeout: Optional[int] = None,
    ):
        return await self.baseRequest(
            method="POST",
            funcname=funcname,
            path=path,
            payload=payload,
            params=params,
            timeout=timeout,
        )

    #
    async def get(
        self,
        funcname: str,
        params: Optional[dict] = None,
        path: str = "/v1/LuaApiCaller",
        timeout: Optional[int] = None,
    ):
        return await self.baseRequest(
            "GET", funcname=funcname, path=path, params=params, timeout=timeout
        )
