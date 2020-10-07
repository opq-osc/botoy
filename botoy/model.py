# pylint: disable=too-many-instance-attributes
class GroupMsg:
    def __init__(self, message: dict):
        self.message: dict = message
        self.CurrentQQ: int = message.get('CurrentQQ')

        temp = message.get('CurrentPacket')
        self.data: dict = temp.get('Data') if temp is not None else {}

        self.FromGroupId: int = self.data.get('FromGroupId')
        self.FromGroupName: str = self.data.get('FromGroupName')
        self.FromUserId: int = self.data.get('FromUserId')
        self.FromNickName: str = self.data.get('FromNickName')
        self.Content: str = self.data.get('Content')
        self.MsgType: str = self.data.get('MsgType')
        self.MsgTime: int = self.data.get('MsgTime')
        self.MsgSeq: int = self.data.get('MsgSeq')
        self.MsgRandom: int = self.data.get('MsgRandom')
        self.RedBaginfo: dict = self.data.get('RedBaginfo')

    def __getitem__(self, key):
        return self.message[key]


class FriendMsg:
    def __init__(self, message: dict):
        self.message: dict = message
        self.CurrentQQ: int = message.get('CurrentQQ')

        temp = message.get('CurrentPacket')
        self.data: dict = temp.get('Data') if temp is not None else {}

        self.FromUin: int = self.data.get('FromUin')
        self.ToUin: int = self.data.get('ToUin')
        self.MsgType: str = self.data.get('MsgType')
        self.MsgSeq: int = self.data.get('MsgSeq')
        self.Content: str = self.data.get('Content')
        self.RedBaginfo: dict = self.data.get('RedBaginfo')

        # 私聊(临时会话)特有
        self.TempUin: int = self.data.get('TempUin')  # 入口群聊ID

    def __getitem__(self, key):
        return self.message[key]


class EventMsg:
    def __init__(self, message: dict):
        self.message: dict = message
        self.CurrentQQ: int = message.get('CurrentQQ')

        temp = message.get('CurrentPacket')
        self.data: dict = temp.get('Data') if temp is not None else {}

        self.EventName: str = self.data.get('EventName')
        self.EventData: dict = self.data.get('EventData')
        self.EventMsg: dict = self.data.get('EventMsg')

        self.Content: str = self.EventMsg.get('Content')
        self.FromUin: int = self.EventMsg.get('FromUin')
        self.MsgSeq: int = self.EventMsg.get('MsgSeq')
        self.MsgType: str = self.EventMsg.get('MsgType')
        self.ToUin: int = self.EventMsg.get('ToUin')
        self.RedBaginfo = self.EventMsg.get('RedBaginfo')

    def __getitem__(self, key):
        return self.message[key]


model_map = {'OnGroupMsgs': GroupMsg, 'OnFriendMsgs': FriendMsg, 'OnEvents': EventMsg}
