import base64
import re


def file_to_base64(path):
    with open(path, 'rb') as f:
        content = f.read()
    return base64.b64encode(content).decode()


def check_schema(url: str) -> str:
    url = url.strip('/')
    if not re.findall(r'(http://|https://)', url):
        return "http://" + url
    return url
