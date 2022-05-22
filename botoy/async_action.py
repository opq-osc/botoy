import mimetypes
import time
import traceback
import uuid
from typing import List, Optional, Union

import httpx

from botoy.parser import event as eventParser

from . import macro, utils
from .config import jconfig
from .log import logger
from .model import EventMsg, FriendMsg, GroupMsg


class AsyncAction:
    def __init__(
        self,
        qq: Optional[int] = None,
        port: Optional[int] = None,
        host: Optional[str] = None,
        timeout: int = 20,
    ):
        self.host = utils.check_schema(host or jconfig.host)
        self.port = port or jconfig.port
        self.address = utils.to_address(self.host, self.port)

        self._qq = int(qq or jconfig.qq or 0)

        self.c = httpx.AsyncClient(
            headers={"Content-Type": "application/json"},
            timeout=timeout + 5,
            base_url=self.address,
            params={"timeout": timeout},
        )

    @property
    async def qq(self) -> int:
        if self._qq == 0:
            self._qq = (await self.getAllBots())[0]
        return self._qq

    @classmethod
    def from_ctx(
        cls, ctx: Union[EventMsg, FriendMsg, GroupMsg], timeout: int = 20
    ) -> "AsyncAction":
        return cls(
            ctx.CurrentQQ,
            host=getattr(ctx, "_host", None),
            port=getattr(ctx, "_port", None),
            timeout=timeout,
        )

    async def close(self):
        return await self.c.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return await self.c.__aexit__(*args)

    ############发送相关############
    async def sendFriendText(self, user: int, content: str) -> dict:
        """发送好友文本消息"""
        return await self.post(
            "SendMsgV2",
            {
                "ToUserUid": user,
                "SendToType": 1,
                "SendMsgType": "TextMsg",
                "Content": content,
            },
        )

    async def sendFriendPic(
        self,
        user: int,
        *,
        picUrl: str = "",
        picBase64Buf: str = "",
        picMd5s: Optional[Union[str, List[str]]] = None,
        content: str = "",
        flashPic=False,
    ):
        """发送好友图片消息"""
        assert any([picUrl, picBase64Buf, picMd5s]), "缺少参数"
        if isinstance(picMd5s, str):
            picMd5s = [picMd5s]
        picMd5s = [  # type: ignore
            {"FileId": 1, "PicMd5": picmd5, "PicSize": 1} for picmd5 in picMd5s or []
        ]
        return await self.post(
            "SendMsgV2",
            {
                "ToUserUid": user,
                "SendToType": 1,
                "SendMsgType": "PicMsg",
                "Content": content,
                "PicUrl": picUrl,
                "PicBase64Buf": picBase64Buf,
                "PicMd5s": picMd5s,
                "FlashPic": flashPic,
            },
        )

    async def sendFriendVoice(
        self, user: int, *, voiceUrl: str = "", voiceBase64Buf: str = ""
    ):
        """发送好友语音消息"""
        assert any([voiceUrl, voiceBase64Buf]), "缺少参数"
        return await self.post(
            "SendMsg",
            {
                "toUser": user,
                "sendToType": 1,
                "sendMsgType": "VoiceMsg",
                "voiceUrl": voiceUrl,
                "voiceBase64Buf": voiceBase64Buf,
            },
        )

    async def sendFriendXml(self, user: int, content: str) -> dict:
        """发送好友Xml消息"""
        return await self.post(
            "SendMsgV2",
            {
                "ToUserUid": user,
                "SendToType": 1,
                "SendMsgType": "XmlMsg",
                "Content": content,
            },
        )

    async def sendFriendTeXiaoText(self, user: int, text: str) -> dict:
        """发送好友特效文本消息"""
        return await self.post(
            "SendMsgV2",
            {
                "ToUserUid": user,
                "SendToType": 1,
                "SendMsgType": "TeXiaoTextMsg",
                "Content": text,
            },
        )

    async def sendGroupText(
        self, group: int, content: str, atUser: Union[int, List[int]] = 0
    ) -> dict:
        """发送群组文本消息"""
        if atUser != 0:
            content = macro.atUser(atUser) + content
        return await self.post(
            "SendMsgV2",
            {
                "ToUserUid": group,
                "SendToType": 2,
                "SendMsgType": "TextMsg",
                "Content": content,
            },
        )

    async def sendGroupPic(
        self,
        group: int,
        *,
        content: str = "",
        picUrl: str = "",
        picBase64Buf: str = "",
        picMd5s: Optional[Union[str, List[str]]] = None,
        flashPic=False,
        atUser: Union[int, List[int]] = 0,
    ) -> dict:
        """发送群组图片消息"""
        assert any([picUrl, picBase64Buf, picMd5s]), "缺少参数"
        if atUser != 0:
            content = macro.atUser(atUser) + content
        if isinstance(picMd5s, str):
            picMd5s = [picMd5s]
        picMd5s = [  # type: ignore
            {"FileId": 1, "PicMd5": picmd5, "PicSize": 1} for picmd5 in picMd5s or []
        ]
        return await self.post(
            "SendMsgV2",
            {
                "ToUserUid": group,
                "SendToType": 2,
                "SendMsgType": "PicMsg",
                "Content": content,
                "PicUrl": picUrl,
                "PicBase64Buf": picBase64Buf,
                "PicMd5s": picMd5s,
                "FlashPic": flashPic,
            },
        )

    async def sendGroupMultiPic(
        self,
        group,
        *items: str,
        text: str = "",
        atUser: Union[int, List[int]] = 0,
    ):
        """发送群多图
        items 支持填写图片http地址和base64，会自动判断类型
        """
        md5s = []
        for item in items:
            if item.startswith("http"):
                info = await self.getGroupPicInfo(url=item)
            else:
                info = await self.getGroupPicInfo(base64=item)
            md5s.append(info["PicInfo"]["PicMd5"])
            time.sleep(0.5)
        return await self.sendGroupPic(group, content=text, atUser=atUser, picMd5s=md5s)

    async def sendGroupVoice(
        self, group: int, *, voiceUrl: str = "", voiceBase64Buf: str = ""
    ) -> dict:
        """发送群组语音消息"""
        assert any([voiceUrl, voiceBase64Buf]), "缺少参数"
        return await self.post(
            "SendMsg",
            {
                "toUser": group,
                "sendToType": 2,
                "sendMsgType": "VoiceMsg",
                "voiceUrl": voiceUrl,
                "voiceBase64Buf": voiceBase64Buf,
            },
        )

    async def sendGroupXml(self, group: int, content: str) -> dict:
        """发送群组Xml消息"""
        return await self.post(
            "SendMsgV2",
            {
                "ToUserUid": group,
                "SendToType": 2,
                "SendMsgType": "XmlMsg",
                "Content": content,
            },
        )

    async def sendGroupJson(self, group: int, content: str) -> dict:
        """发送群组Json消息"""
        return await self.post(
            "SendMsgV2",
            {
                "ToUserUid": group,
                "SendToType": 2,
                "SendMsgType": "JsonMsg",
                "Content": content,
            },
        )

    async def sendGroupTeXiaoText(self, group: int, text: str) -> dict:
        """发送群组特效文本消息"""
        return await self.post(
            "SendMsgV2",
            {
                "ToUserUid": group,
                "SendToType": 2,
                "SendMsgType": "TeXiaoTextMsg",
                "Content": text,
            },
        )

    async def sendPrivateText(self, user: int, group: int, content: str) -> dict:
        """发送私聊文本消息"""
        return await self.post(
            "SendMsgV2",
            {
                "ToUserUid": user,
                "GroupID": group,
                "SendToType": 3,
                "SendMsgType": "TextMsg",
                "Content": content,
            },
        )

    async def sendPrivateXml(self, user: int, group: int, content: str) -> dict:
        """发送私聊Xml消息"""
        return await self.post(
            "SendMsgV2",
            {
                "ToUserUid": user,
                "GroupID": group,
                "SendToType": 3,
                "SendMsgType": "XmlMsg",
                "Content": content,
            },
        )

    async def sendPrivateVoice(
        self, user: int, group: int, *, voiceUrl: str = "", voiceBase64Buf: str = ""
    ) -> dict:
        assert any([voiceUrl, voiceBase64Buf]), "缺少参数"
        return await self.post(
            "SendMsg",
            {
                "toUser": user,
                "sendToType": 3,
                "sendMsgType": "VoiceMsg",
                "content": "",
                "groupid": group,
                "voiceUrl": voiceUrl,
                "voiceBase64Buf": voiceBase64Buf,
            },
        )

    async def sendPrivatePic(
        self,
        user: int,
        group: int,
        content: str = "",
        *,
        picUrl: str = "",
        picBase64Buf: str = "",
        picMd5s: Optional[Union[str, List[str]]] = None,
    ) -> dict:
        """发送私聊图片消息"""
        assert any([picUrl, picBase64Buf, picMd5s]), "缺少参数"
        if isinstance(picMd5s, str):
            picMd5s = [picMd5s]
        picMd5s = [  # type: ignore
            {"FileId": 1, "PicMd5": picmd5, "PicSize": 1} for picmd5 in picMd5s or []
        ]
        return await self.post(
            "SendMsgV2",
            {
                "ToUserUid": user,
                "GroupID": group,
                "SendToType": 3,
                "SendMsgType": "PicMsg",
                "Content": content,
                "PicUrl": picUrl,
                "PicBase64Buf": picBase64Buf,
                "PicMd5s": picMd5s,
            },
        )

    async def sendPhoneText(self, content: str) -> dict:
        """给手机发文字"""
        return await self.post(
            "SendMsgV2",
            {"SendToType": 2, "SendMsgType": "PhoneMsg", "Content": content},
        )

    async def replyGroupMsg(
        self,
        group: int,
        content: str,
        msgSeq: int,
        msgTime: Optional[int] = None,
        user: int = 0,
        rawContent: str = "",
    ):
        """发送回复消息, 回复群消息
        下面的原消息表示需要回复的消息
        :param group: 原消息的群号
        :param content: 回复内容
        :param msgSeq: 原消息的msgSeq, 点击跳转到该条消息位置
        :param msgTime: 原消息的msgTime, 如果不指定，默认为当前时间戳
        :param user: 原消息的人的qq号，也可以是其他人，该用户收到消息会提示“有新回复”, 默认为0
        :param rawContent: 原消息内容，可以任意指定，默认为空
        """
        return await self.post(
            "SendMsg",
            {
                "toUser": group,
                "sendToType": 2,
                "sendMsgType": "ReplayMsg",
                "content": content,
                "replayInfo": {
                    "MsgSeq": msgSeq,
                    "MsgTime": msgTime or int(time.time()),
                    "UserID": user,
                    "RawContent": rawContent,
                },
            },
        )

    async def replyFriendMsg(
        self,
        user: int,
        content: str,
        msgSeq: int,
        msgTime: Optional[int] = None,
        rawContent: str = "",
    ):
        """发送回复消息, 回复好友消息
        下面的原消息表示需要回复的消息
        :param user: 原消息发送人
        :param content: 回复内容
        :param msgSeq: 原消息的msgSeq, 点击跳转到该条消息位置
        :param msgTime: 原消息的msgTime, 如果不指定，默认为当前时间戳
        :param rawContent: 原消息内容，可以任意指定，默认为空
        """
        return await self.post(
            "SendMsg",
            {
                "toUser": user,
                "sendToType": 1,
                "sendMsgType": "ReplayMsg",
                "content": content,
                "replayInfo": {
                    "MsgSeq": msgSeq,
                    "MsgTime": msgTime or int(time.time()),
                    "UserID": user,
                    "RawContent": rawContent,
                },
            },
        )

    async def poke(self, user: int, group=0):
        """戳一戳，未设置群ID就是戳好友"""
        payload = {"UserID": user, "GroupID": group}
        if group == 0:
            payload["Type"] = 0
        else:
            payload["Type"] = 1
        return await self.post("OidbSvc.0xed3_1", payload)

    async def repostVideo2Group(self, group: int, forwordBuf: str) -> dict:
        """转发视频到群聊
        :param group: 群号
        :param forwordBuf: 原视频的forwordBuf字段
        """
        return await self.post(
            "SendMsg",
            {
                "toUser": group,
                "sendToType": 2,
                "sendMsgType": "ForwordMsg",
                "forwordBuf": forwordBuf,
                "forwordField": 19,
            },
        )

    async def getVideoURL(self, group: int, videoMD5: str, videoURL: str) -> dict:
        """获取视频链接
        :param group: 群号
        :param videoMD5: 视频的 MD5 值，可以从上报的消息中获得
        :param videoURL: 上报的消息中传给的 url 值
        """
        return await self.post(
            "PttCenterSvr.ShortVideoDownReq",
            {"GroupID": group, "VideoUrl": videoURL, "VideoMd5": videoMD5},
        )

    async def getFriendFileURL(self, fileID: str) -> dict:
        """获取好友文件链接
        :param fileID: 文件 ID，可由上报的消息中获得
        """
        return await self.post(
            "OfflineFilleHandleSvr.pb_ftn_CMD_REQ_APPLY_DOWNLOAD-1200",
            {"FileID": fileID},
        )

    async def getGroupFileURL(self, group: int, fileID: str) -> dict:
        """获取好友文件链接
        :param group: 群号
        :param fileID: 文件 ID，可由上报的消息中获得
        """
        return await self.post(
            "OidbSvc.0x6d6_2",
            {"GroupID": group, "FileID": fileID},
        )

    async def repostVideo2Friend(self, user: int, forwordBuf: str) -> dict:
        """转发视频到好友
        :param user: 好友QQ
        :param forwordBuf: 原视频的forwordBuf字段
        """
        return await self.post(
            "SendMsg",
            {
                "toUser": user,
                "sendToType": 1,
                "sendMsgType": "ForwordMsg",
                "forwordBuf": forwordBuf,
                "forwordField": 19,
            },
        )

    async def groupJoinAuth(self, ctx: EventMsg, cmd=None):
        """
        :param ctx: 事件EventMsg, 类型不匹配将报错
        :param cmd: True:同意进群,False:拒绝,None:忽略
        """
        join_group_info = eventParser.group_adminsysnotify(ctx)
        assert join_group_info, "事件类型不匹配"
        return await self.post(
            "AnswerInviteGroup",
            {
                "Seq": join_group_info.Seq,
                "Who": join_group_info.Who,
                "Flag_7": join_group_info.Flag_7,
                "Flag_8": join_group_info.Flag_8,
                "GroupId": join_group_info.GroupId,
                "Action": {True: 11, False: 12, None: 14}[
                    cmd
                ],  # 11 agree , 14 忽略 , 12/21 disagree
            },
        )

    async def uploadGroupFile(
        self,
        group: int,
        fileURL: str = "",
        fileBase64: str = "",
        filePath: str = "",
        fileName: str = "",
        fileType: str = "",
        notify: bool = True,
    ) -> dict:
        """上传群文件
        :param group: 群号
        :param fileURL: 文件网络地址, 和fileBase64二选一
        :param fileBase64: 文件base64编码, 和fileURL二选一
        :param filePath: 文件路径，注意该路径要确保机器人服务端能够访问到，并且该项设置后，fileName和fileType参数将无效
        :param fileName: 文件名(需包含拓展名)，如果不传则随机生成并且如果是使用URL上传则会尝试自动推测文件类型
        :param fileType: 文件的后缀名，如果指定了，会自动加在文件名(fileName)后面, 如 .txt 或 txt
        :param notify: 是否通知
        """
        # 将filePath作最高优先级，因为通过路径上传，fileName字段无效
        if not filePath:
            if not fileName:
                fileName = str(uuid.uuid4())
                # guess extension by url
                if fileURL:
                    try:
                        async with httpx.AsyncClient() as client:
                            async with client.stream("GET", fileURL, timeout=5) as resp:
                                content_type = resp.headers["content-type"]
                                extension = mimetypes.guess_extension(content_type)
                                if extension is not None:
                                    fileName = fileName + extension
                    except Exception:
                        pass
            if fileType:
                if fileType.startswith("."):
                    fileName = fileName + fileType
                else:
                    fileName = fileName + "." + fileType
        payload = {
            "ToUserUid": group,
            "SendMsgType": "UploadGroupFile",
            "FileName": fileName,
            "Notify": notify,
        }
        if filePath:
            payload.update({"FilePath": filePath})
        elif fileURL:
            payload.update({"FileUrl": fileURL})
        elif fileBase64:
            payload.update({"FileBase64": fileBase64})
        else:
            raise Exception("fileURL, fileBase64, filePath 必须给定其中一个")
        return await self.post("SendMsgV2", payload)

    async def openRedBag(self, redBagInfo: dict):
        """打开红包

        :param redBagInfo: 红包信息, ctx.RedBaginfo
        """
        return await self.post("OpenRedBag", redBagInfo)

    async def getCookies(self) -> dict:
        """获取QQ相关cookie"""
        return await self.get("GetUserCook")

    async def getUserInfo(self, user: int) -> dict:
        """获取用户信息昵称头像等"""
        return await self.post("GetUserInfo", {"UserID": user})

    async def getSummaryCard(self, user: int) -> dict:
        """获取企鹅卡片资料"""
        return await self.post("SummaryCard.ReqSummaryCard", {"UserID": user})

    async def getUserList(self) -> List[dict]:
        """获取好友列表"""
        friend_list = []
        start_index = 0
        while True:
            data = await self.post("GetQQUserList", {"StartIndex": start_index})
            if "Friendlist" not in data:
                break
            friend_list.extend(data["Friendlist"])
            if len(friend_list) >= int(data.get("Totoal_friend_count", 0)):  # 这里有个拼写错误
                break
            if "GetfriendCount" not in data:
                break
            start_index += int(
                data.get("GetfriendCount", 999999)
            )  # 设置 999999 为了在 API 坏了的情况下能跳出循环
        return friend_list

    async def getGroupList(self) -> List[dict]:
        """获取群列表"""
        next_token = ""
        group_list = []
        while True:
            data = await self.post("GetGroupList", {"NextToken": next_token})
            if "TroopList" not in data:
                break
            group_list.extend(data["TroopList"])
            next_token = data.get("NextToken", "")
            if not next_token:
                break
        return group_list

    async def getGroupMembers(self, group: int) -> List[dict]:
        """获取群成员列表"""
        members = []
        lastUin = 0
        while True:
            data = await self.post(
                "GetGroupUserList", {"GroupUin": group, "LastUin": lastUin}
            )
            if "MemberList" in data:
                members.extend(data["MemberList"])
            if "LastUin" not in data or data["LastUin"] == 0:
                break
            lastUin = data["LastUin"]
            time.sleep(0.6)
        return members

    async def getGroupAdminList(self, group: int, include_owner=True) -> List[dict]:
        """获取群管理员列表
        :param group: 群号
        :param include_owner: 是否包括群主
        """
        members = await self.getGroupMembers(group)
        if include_owner:
            # 获取群主id
            owner = 0
            for groupInfo in await self.getGroupList():
                if groupInfo["GroupId"] == group:
                    owner = groupInfo["GroupOwner"]
                    break
            admins = [
                member
                for member in members
                if member["GroupAdmin"] == 1 or member["MemberUin"] == owner
            ]
        else:
            admins = [member for member in members if member["GroupAdmin"] == 1]
        return admins

    async def getClusterInfo(self) -> dict:
        """获取当前集群信息"""
        return await self.get("", path="/v1/ClusterInfo", params={"isShow": 1, "qq": 1})

    async def setUniqueTitle(self, user: int, group: int, title: str):
        """设置群头衔"""
        return await self.post(
            "OidbSvc.0x8fc_2",
            {"GroupID": group, "UserID": user, "NewTitle": title},
        )

    async def modifyGroupCard(self, user: int, group: int, nick: str):
        """修改群名片"""
        return await self.post(
            "ModifyGroupCard", {"UserID": user, "GroupID": group, "NewNick": nick}
        )

    async def shutUserUp(self, groupID: int, userid: int, ShutTime: int):
        """禁言用户(禁言时间单位为分钟 ShutTime=0 取消禁言)"""
        return await self.post(
            "ShutUp",
            {
                "ShutUpType": 0,
                "GroupID": groupID,
                "ShutUid": userid,
                "ShutTime": ShutTime,
            },
        )

    async def shutAllUp(self, group: int, switch: int):
        """全体禁言
        :param switch: 1 开启; 0 关闭
        """
        return await self.post(
            "OidbSvc.0x89a_0",
            {"GroupID": group, "Switch": switch},
        )

    async def setGroupAnnounce(
        self,
        group: int,
        text: str,
        pinned: bool = False,
        title: str = "",
        typ: bool = True,
    ):
        """设置群公告
        :param group: 群号
        :param text: 内容
        :param pinned: 是否置顶
        :param title: 标题,可以空
        :param typ: 是否发送新成员
        """
        return await self.post(
            path="/v1/Group/Announce",
            funcname="",
            payload={
                "GroupID": group,
                "Title": title,
                "Text": text,
                "Pinned": 1 if pinned else 0,
                "Type": 20 if typ else 10,  # 20 发给新成员, 10 弹窗
            },
        )

    async def likeUser(self, user: int, cmd=0) -> dict:
        """给某人点赞
        :param user: 用户QQ号
        :param cmd: 发送包选项, 0 或 1; 0表示使用``QQZan``; 1表示使用``OidbSvc.0x7e5_4``, 默认为0
        """
        return await self.post(
            "QQZan" if cmd == 0 else "OidbSvc.0x7e5_4", {"UserID": user}
        )

    async def toggleGroupAdmin(self, user: int, group: int, flag=1) -> dict:
        """设置和取消群管理员
        :param user: 用户QQ
        :param group: 群号
        :param flag: 1 或 0, 1表示设置为管理员; 0 表示取消管理员, 默认为1
        """
        return await self.post(
            "OidbSvc.0x55c_1",
            {"GroupID": group, "UserID": user, "Flag": 0 if flag == 0 else 1},
        )

    async def revokeGroupMsg(self, group: int, msgSeq: int, msgRandom: int) -> dict:
        """撤回群消息
        :param group: 群号
        :param msgSeq: 消息msgSeq
        :param msgRandom: 消息msgRandom
        """
        return await self.post(
            "RevokeMsg", {"GroupID": group, "MsgSeq": msgSeq, "MsgRandom": msgRandom}
        )

    async def revoke(self, ctx: GroupMsg):
        """撤回群消息"""
        return await self.revokeGroupMsg(ctx.FromGroupId, ctx.MsgSeq, ctx.MsgRandom)

    async def inviteUserJoinGroup(self, group: int, user: int) -> dict:
        """拉人入群
        :param group: 哪个群?
        :param user: 拉谁?
        """
        return await self.post(
            "GroupMgr",
            {"ActionType": 8, "GroupID": group, "ActionUserID": user, "Content": ""},
        )

    async def joinGroup(self, group: int, content: str = "") -> dict:
        """加入群聊
        :param group: 哪个群?
        :param content: 加群理由
        """
        return await self.post(
            "GroupMgr",
            {"ActionType": 1, "GroupID": group, "ActionUserID": 0, "Content": content},
        )

    async def exitGroup(self, group: int) -> dict:
        """退出群聊
        :param group: 哪个群?
        """
        return await self.post(
            "GroupMgr",
            {"ActionType": 2, "GroupID": group, "ActionUserID": 0, "Content": ""},
        )

    async def driveUserAway(self, group: int, user: int) -> dict:
        """移出群聊
        :param group: 哪个群?
        :param user:把谁踢出去?
        """
        return await self.post(
            "GroupMgr",
            {"ActionType": 3, "GroupID": group, "ActionUserID": user, "Content": ""},
        )

    async def refreshKeys(self) -> dict:
        """刷新key二次登陆"""
        return await self.get("", path="/v1/RefreshKeys")

    async def dealFriend(self, ctx: EventMsg, cmd=None) -> dict:
        """处理好友请求
        :param ctx: 事件EventMsg, 类型不匹配将报错
        :param cmd: True:同意,False:拒绝,None:忽略
        """
        friend_add_info = eventParser.friend_add(ctx)
        assert friend_add_info, "事件类型不匹配"
        return await self.post(
            "DealFriend",
            {
                "UserID": friend_add_info.UserID,
                "FromType": friend_add_info.FromType,
                "Type": friend_add_info.Type,
                "Field_3": friend_add_info.Field_3,
                "Field_8": friend_add_info.Field_8,
                "Content": friend_add_info.Content,
                "FromGroupId": friend_add_info.FromGroupId,
                "FromGroupName": friend_add_info.FromGroupName,
                "Action": {True: 2, False: 3, None: 1}[cmd],  # 1忽略2同意3拒绝
            },
        )

    async def logout(self, flag=False) -> dict:
        """退出指定QQ
        :param flag: 是否删除设备信息文件
        """
        return await self.post("LogOut", {"Flag": flag})

    async def getGroupPicInfo(self, url: str = "", base64: str = ""):
        """上传群图片获取图片信息
        :param url: 图片链接
        :param base64: 图片base64
        """
        assert any([url, base64]), "缺少参数"
        return await self.post(
            "", {"PicUrl": url, "PicBase64Buf": base64}, path="/v1/GetGroupPicInfo"
        )

    async def updateAvatar(self, url: str):
        """上传头像
        :param url: 图片链接
        """
        return await self.post("", {"HDIMGUrl": url}, path="/v1/SelfHDIMG")

    async def getAllBots(self) -> List[int]:
        """获取OPQ登陆的所有机器人QQ号"""
        return [i["QQ"] for i in (await self.getClusterInfo())["QQUsers"]]

    ############################################################################
    async def baseRequest(
        self,
        method: str,
        funcname: str,
        path: str,
        payload: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """基础请求方法, 提供部分提示信息，出错返回空字典，其他返回服务端响应结果"""
        params = params or {}
        params["funcname"] = funcname
        if not params.get("qq"):
            params["qq"] = await self.qq

        # 发送请求
        try:
            resp = await self.c.request(
                method, httpx.URL(url=path, params=params), json=payload
            )
            resp.raise_for_status()
        except httpx.TimeoutException:
            logger.warning(f"响应超时，但不代表处理未成功, 结果未知!")
            return {}
        except httpx.HTTPStatusError:
            logger.error(
                f"响应码出错 => {resp.status_code}，大概率是因为账号已离线或者qq号错误",  # type:ignore
            )
            return {}
        except Exception:
            logger.error(f"请求出错: {traceback.format_exc()}")
            return {}

        # 处理数据
        try:
            data = resp.json()
        except Exception:
            logger.error("API响应结果非json格式")
            return {}

        if data is None:
            logger.error("返回为null, 该类情况多数是因为响应超时或者该API不存在，或服务端操作超时(此时不代表未成功)")
            return {}

        # 返回码提示
        if "Ret" in data:
            ret = data.get("Ret")
            if ret == 0:
                pass
            elif ret == 34:
                logger.error(f"未知错误，跟消息长度似乎无关，可以尝试分段重新发送 => {data}")
            elif ret == 110:
                logger.error(f"发送失败，你已被移出该群，请重新加群 => {data}")
            elif ret == 120:
                logger.error(f"机器人被禁言 => {data}")
            elif ret == 241:
                logger.error(f"消息发送频率过高，对同一个群或好友，建议发消息的最小间隔控制在1100ms以上 => {data}")
            elif ret == 299:
                logger.error(f"超过群发言频率限制 => {data}")
            else:
                logger.error(f"请求发送成功, 但处理失败 => {data}")

        return data

    async def post(
        self,
        funcname: str,
        payload: dict,
        params: Optional[dict] = None,
        path: str = "/v1/LuaApiCaller",
    ) -> dict:
        """封装常用的post操作"""
        return await self.baseRequest(
            "POST", funcname=funcname, path=path, payload=payload, params=params
        )

    async def get(
        self,
        funcname: str,
        params: Optional[dict] = None,
        path: str = "/v1/LuaApiCaller",
    ) -> dict:
        """封装get操作"""
        return await self.baseRequest(
            "GET", funcname=funcname, path=path, params=params
        )
