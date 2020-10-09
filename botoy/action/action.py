import traceback
from json import JSONDecodeError
from typing import List, Union

import httpx

from botoy import macro
from botoy.config import Config
from botoy.log import logger


class Action:
    def __init__(self, qq: int, port: int = None, host: str = None, timeout=20):
        self.qq = qq
        self.config = Config(host=host, port=port)
        self.c = httpx.Client(
            headers={'Content-Type': 'application/json'},
            timeout=timeout + 5,
            base_url=self.config.address,
            params={'qq': self.qq, 'timeout': timeout},
        )

    ############发送相关############
    def sendFriendText(self, user: int, content: str) -> dict:
        """发送好友文本消息"""
        return self.post(
            'SendMsgV2',
            {
                "ToUserUid": user,
                "SendToType": 1,
                "SendMsgType": "TextMsg",
                "Content": content,
            },
        )

    def sendFriendPic(
        self,
        user: int,
        *,
        picUrl: str = '',
        picBase64Buf: str = '',
        fileMd5: str = '',
        content: str = '',
        flashPic=False,
    ):
        """发送好友图片消息"""
        assert any([picUrl, picBase64Buf, fileMd5]), '缺少参数'
        return self.post(
            'SendMsg',
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

    def sendFriendVoice(
        self, user: int, *, voiceUrl: str = '', voiceBase64Buf: str = ''
    ):
        """发送好友语音消息"""
        assert any([voiceUrl, voiceBase64Buf]), '缺少参数'
        return self.post(
            'SendMsg',
            {
                "toUser": user,
                "sendToType": 1,
                "sendMsgType": "VoiceMsg",
                "voiceUrl": voiceUrl,
                "voiceBase64Buf": voiceBase64Buf,
            },
        )

    def sendFriendXml(self, user: int, content: str) -> dict:
        """发送好友Xml消息"""
        return self.post(
            'SendMsgV2',
            {
                "ToUserUid": user,
                "SendToType": 1,
                "SendMsgType": "XmlMsg",
                "Content": content,
            },
        )

    def sendGroupText(
        self, group: int, content: str, atUser: Union[int, List[int]] = 0
    ) -> dict:
        """发送群组文本消息"""
        if atUser != 0:
            content = macro.atUser(atUser) + content
        return self.post(
            'SendMsgV2',
            {
                "ToUserUid": group,
                "SendToType": 2,
                "SendMsgType": "TextMsg",
                "Content": content,
            },
        )

    def sendGroupPic(
        self,
        user: int,
        *,
        content: str = '',
        picUrl: str = '',
        picBase64Buf: str = '',
        fileMd5: str = '',
        flashPic=False,
        atUser: Union[int, List[int]],
    ) -> dict:
        """发送群组图片消息"""
        assert any([picUrl, picBase64Buf, fileMd5]), '缺少参数'
        if atUser != 0:
            content = macro.atUser(atUser) + content
        return self.post(
            'SendMsg',
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

    def sendGroupVoice(
        self, group: int, *, voiceUrl: str = '', voiceBase64Buf: str = ''
    ) -> dict:
        """发送群组语音消息"""
        assert any([voiceUrl, voiceBase64Buf]), '缺少参数'
        return self.post(
            'SendMsg',
            {
                "toUser": group,
                "sendToType": 2,
                "sendMsgType": "VoiceMsg",
                "voiceUrl": voiceUrl,
                "voiceBase64Buf": voiceBase64Buf,
            },
        )

    def sendGroupXml(self, group: int, content: str) -> dict:
        """发送群组Xml消息"""
        return self.post(
            'SendMsgV2',
            {
                "ToUserUid": group,
                "SendToType": 2,
                "SendMsgType": "XmlMsg",
                "Content": content,
            },
        )

    def sendGroupJson(self, group: int, content: str) -> dict:
        """发送群组Json消息"""
        return self.post(
            'SendMsgV2',
            {
                "ToUserUid": group,
                "SendToType": 2,
                "SendMsgType": "JsonMsg",
                "Content": content,
            },
        )

    def sendPrivateText(self, user: int, group: int, content: str) -> dict:
        """发送私聊文本消息"""
        return self.post(
            'SendMsgV2',
            {
                "ToUserUid": user,
                "GroupID": group,
                "SendToType": 3,
                "SendMsgType": "TextMsg",
                "Content": content,
            },
        )

    def sendPrivateXml(self, user: int, group: int, content: str) -> dict:
        """发送私聊Xml消息"""
        return self.post(
            'SendMsgV2',
            {
                "ToUserUid": user,
                "GroupID": group,
                "SendToType": 3,
                "SendMsgType": "XmlMsg",
                "Content": content,
            },
        )

    def sendPrivateVoice(
        self, user: int, group: int, *, voiceUrl: str = '', voiceBase64Buf: str = ''
    ) -> dict:
        assert any([voiceUrl, voiceBase64Buf]), '缺少参数'
        return self.post(
            'SendMsg',
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

    def sendPrivatePic(
        self,
        user: int,
        group: int,
        content: str = '',
        *,
        picUrl: str = '',
        picBase64Buf: str = '',
        fileMd5: str = '',
    ) -> dict:
        """发送私聊图片消息"""
        assert any([picUrl, picBase64Buf, fileMd5]), '缺少参数'
        return self.post(
            'SendMsg',
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

    def sendPhoneText(self, content: str):
        """给手机发文字"""
        return self.post(
            'SendMsgV2',
            {"SendToType": 2, "SendMsgType": "PhoneMsg", "Content": content},
        )

    ############获取############
    def getCookies(self):
        """获取QQ相关cookie"""
        return self.get('GetUserCook')

    def getUserList(self):  # todo:循环获取
        """获取好友列表"""
        return self.post('GetQQUserList', {'StartIndex': 0})

    def getUserInfo(self, UserID: int):
        """获取任意用户信息昵称头像等"""
        return self.post('GetUserInfo', {'UserID': UserID})

    def getGroupList(self):  # todo:循环获取
        """获取当前bot加入的群列表"""
        return self.post('GetGroupList', {'NextToken': ''})

    def getGroupUserList(self, group: int):  # todo:循环获取
        """获取群信息(bot已经加入的,未加入的获取不到)"""
        return self.post('GetGroupUserList', {'GroupUin': group, 'LastUin': ''})

    ############操作############
    def setUniqueTitle(self, user: int, group: int, title: str) -> dict:
        """设置群头衔"""
        return self.post(
            'OidbSvc.0x8fc_2',
            {"GroupID": group, "UserID": user, "NewTitle": title},
        )

    def modifyGroupCard(self, user: int, group: int, nick: str) -> dict:
        """修改群名片"""
        return self.post(
            'ModifyGroupCard', {'UserID': user, 'GroupID': group, 'NewNick': nick}
        )

    def shutUserUp(self, groupID: int, userid: int, ShutTime: int) -> dict:
        """禁言用户(禁言时间单位为分钟 ShutTime=0 取消禁言)"""
        return self.post(
            'ShutUp',
            {
                'ShutUpType': 0,
                'GroupID': groupID,
                'ShutUid': userid,
                'ShutTime': ShutTime,
            },
        )

    def shutAllUp(self, group: int, switch: int):
        """全体禁言
        :param switch: 1 开启; 0 关闭
        """
        return self.post(
            'OidbSvc.0x89a_0',
            {"GroupID": group, "Switch": switch},
        )

    def setGroupAnnounce(
        self,
        group: int,
        text: str,
        pinned: bool = False,
        title: str = '',
        typ: bool = True,
    ):
        """设置群公告
        :param group: 群号
        :param text: 内容
        :param pinned: 是否置顶
        :param title: 标题,可以空
        :param typ: 是否发送新成员
        """
        return self.post(
            path='/v1/Group/Announce',
            funcname='',
            payload={
                "GroupID": group,
                "Title": title,
                "Text": text,
                "Pinned": 1 if pinned else 0,
                "Type": 20 if typ else 10,  # 20 发给新成员, 10 弹窗
            },
        )

    ############################################################################
    def baseRequest(
        self,
        method: str,
        funcname: str,
        path: str,
        payload: dict = None,
        params: dict = None,
    ) -> dict:
        """基础请求方法, 提供部分提示信息，出错返回空字典，其他返回服务端响应结果"""
        if params is not None:
            params = params.update({'funcname': funcname})
        else:
            params = {'funcname': funcname}

        # 发送请求
        try:
            resp = self.c.request(
                method, httpx.URL(url=path, params=params), json=payload
            )
            resp.raise_for_status()
        except httpx.RequestError as e:
            if isinstance(e, httpx.Timeout):
                logger.warning('响应超时，但不代表处理未成功, 结果未知!')
            else:
                logger.error(f'请求出错: {traceback.format_exc()}')
            return {}

        # 处理数据
        try:
            data = resp.json()
        except JSONDecodeError as e:
            logger.error('API响应结果非json格式')
            return {}

        if data is None:
            logger.error('返回为null')
            return {}

        # 返回码提示
        if 'Ret' in data:
            ret = data.get('Ret')
            if ret == 0:
                pass
            elif ret == 34:
                logger.error(f'未知错误，跟消息长度似乎无关，可以尝试分段重新发送 => {data}')
            elif ret == 110:
                logger.error(f'发送失败，你已被移出该群，请重新加群 => {data}')
            elif ret == 120:
                logger.error(f'机器人被禁言 => {data}')
            elif ret == 241:
                logger.error(f'消息发送频率过高，对同一个群或好友，建议发消息的最小间隔控制在1100ms以上 => {data}')
            elif ret == 299:
                logger.error(f'超过群发言频率限制 => {data}')
            else:
                logger.error(f'请求发送成功, 但处理失败 => {data}')

        return data

    def post(
        self,
        funcname: str,
        payload: dict,
        params: dict = None,
        path: str = '/v1/LuaApiCaller',
    ) -> dict:
        """封装常用的post操作"""
        return self.baseRequest(
            'POST', funcname=funcname, path=path, payload=payload, params=params
        )

    def get(
        self,
        funcname: str,
        params: dict = None,
        path: str = '/v1/LuaApiCaller',
    ) -> dict:
        """封装get操作"""
        return self.baseRequest('GET', funcname=funcname, path=path, params=params)
