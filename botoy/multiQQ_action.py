import httpx
import time
from botoy.config import jconfig
from .action import Action

from . import utils

url=f"{jconfig.host}:{jconfig.port}"

def getClusterInfo():
    ###获取全部QQ号信息
    return httpx.get(f"{url}/v1/ClusterInfo?isShow=1").json()

def getQQlist():
    data= getClusterInfo()
    qqlist = []
    for i in data["QQUsers"]:
        qqlist.append(i["QQ"])
    return qqlist

def sendAllGroupText(content:str):
    qqlist=getQQlist()
    for i in qqlist:
        grouplist = Action(qq=i).getGroupList()
        list = []
        for j in grouplist:
            list.append(j['GroupId'])
        print(list)
        for k in list:
            Action(qq=i).sendGroupText(group=k,content=content)
            time.sleep(3)


def sendAllGroupPic(
    content: str = "",
    picUrl: str = "",
    picBase64Buf: str = "",):
    qqlist =getQQlist()
    for i in qqlist:
        grouplist = Action(qq=i).getGroupList()
        list = []
        for j in grouplist:
            list.append(j['GroupId'])
        print(list)
        for k in list:
            Action(qq=i).sendGroupPic(group=k,content=content,picUrl=picUrl,picBase64Buf=picBase64Buf)
            time.sleep(3)

