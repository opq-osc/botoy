import time
import traceback
from typing import List, Union

import httpx

from botoy import macro
from botoy.config import Config
from botoy.log import logger
from botoy.model import EventMsg, FriendMsg, GroupMsg


class AsyncAction:
    def __init__(
        self, qq: int = None, port: int = None, host: str = None, timeout: int = 20
    ):
        self.config = Config(host=host, port=port)

        self.qq = int(qq or self.config.qq)

        self.c = httpx.AsyncClient(
            headers={"Content-Type": "application/json"},
            timeout=timeout + 5,
            base_url=self.config.address,
            params={"qq": self.qq, "timeout": timeout},
        )

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
        fileMd5: str = "",
        content: str = "",
        flashPic=False,
    ):
        """发送好友图片消息"""
        assert any([picUrl, picBase64Buf, fileMd5]), "缺少参数"
        return await self.post(
            "SendMsg",
            {
                "toUser": user,
                "sendToType": 1,
                "sendMsgType": "PicMsg",
                "content": content,
                "picUrl": picUrl,
                "picBase64Buf": picBase64Buf,
                "fileMd5": fileMd5,
                "flashPic": flashPic,
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
        user: int,
        *,
        content: str = "",
        picUrl: str = "",
        picBase64Buf: str = "",
        fileMd5: str = "",
        flashPic=False,
        atUser: Union[int, List[int]] = 0,
    ) -> dict:
        """发送群组图片消息"""
        assert any([picUrl, picBase64Buf, fileMd5]), "缺少参数"
        if atUser != 0:
            content = macro.atUser(atUser) + content
        return await self.post(
            "SendMsg",
            {
                "toUser": user,
                "sendToType": 2,
                "sendMsgType": "PicMsg",
                "content": content,
                "picUrl": picUrl,
                "picBase64Buf": picBase64Buf,
                "fileMd5": fileMd5,
                "flashPic": flashPic,
            },
        )

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
        fileMd5: str = "",
    ) -> dict:
        """发送私聊图片消息"""
        assert any([picUrl, picBase64Buf, fileMd5]), "缺少参数"
        return await self.post(
            "SendMsg",
            {
                "toUser": user,
                "sendToType": 3,
                "sendMsgType": "PicMsg",
                "content": content,
                "groupid": group,
                "picUrl": picUrl,
                "picBase64Buf": picBase64Buf,
                "fileMd5": fileMd5,
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
        msgTime: int = None,
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
        msgTime: int = None,
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

    async def groupJoinAuth(self, seq: int, group: int, userid: int, cmd=None):
        """
        :param Seq:  GroupAdminsysnotify消息中的Seq
        :param group: QQ群号
        :param userid: 申请进群的QQ号
        :param cmd: True:同意进群,False:拒绝,None:忽略
        :return:
        """
        return await self.post(
            "AnswerInviteGroup",
            {
                "Seq": seq,
                "Who": userid,
                "Flag_7": 3,  # 这2个flag不知道会不会变
                "Flag_8": 21,
                "GroupId": group,
                "Action": {True: 11, False: 12, None: 14}[
                    cmd
                ],  # 11 agree , 14 忽略 , 12/21 disagree
            },
        )

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

    async def baseRequest(
        self,
        method: str,
        funcname: str,
        path: str,
        payload: dict = None,
        params: dict = None,
    ) -> dict:
        """基础请求方法, 提供部分提示信息，出错返回空字典，其他返回服务端响应结果"""
        if params is not None:
            params.update({"funcname": funcname})
        else:
            params = {"funcname": funcname}

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
                f"响应码出错 => {resp.status_code}",  # type:ignore
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
        params: dict = None,
        path: str = "/v1/LuaApiCaller",
    ) -> dict:
        """封装常用的post操作"""
        return await self.baseRequest(
            "POST", funcname=funcname, path=path, payload=payload, params=params
        )

    async def get(
        self,
        funcname: str,
        params: dict = None,
        path: str = "/v1/LuaApiCaller",
    ) -> dict:
        """封装get操作"""
        return await self.baseRequest(
            "GET", funcname=funcname, path=path, params=params
        )
