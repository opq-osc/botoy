"""提供框架所需的通用函数"""
import base64
import re


def check_schema(url: str) -> str:
    url = url.strip("/")
    if not re.findall(r"(http://|https://)", url):
        return "http://" + url
    return url


def file_to_base64(path):
    """获取文件base64编码"""
    with open(path, "rb") as f:
        content = f.read()
    return base64.b64encode(content).decode()
