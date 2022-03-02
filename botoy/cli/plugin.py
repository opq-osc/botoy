import base64
import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import click
import httpx

plugin: click.Group

echo = click.echo


PLUGIN_DIR = Path("plugins")


@click.group()
def plugin():
    """插件管理

    安装 install --help

    移除 remove --help

    列表 list --help
    """


def _git_cmd():
    ret = None

    def f() -> List[str]:
        nonlocal ret
        if not ret:
            try:
                if (
                    subprocess.run(
                        ["git", "version"], stdout=subprocess.DEVNULL
                    ).returncode
                    == 0
                ):
                    ret = ["git", "clone"]
            except Exception:
                pass
        if not ret:
            echo("请安装 git !")
            exit(1)
        return ret

    return f


git_cmd = _git_cmd()


def check_plugin_exists(name: str):
    if not name.startswith("bot_"):
        name = "bot_" + name
    return (PLUGIN_DIR / name).exists() or (PLUGIN_DIR / f"{name}.py").exists()


def strip_plugin_name(name: str):
    if name.startswith("bot_"):
        return name[4:]
    return name


# name 应该不已bot_开头
def install_plugin(src: str, name: Optional[str], data: dict):
    echo("")
    # 直接克隆仓库
    findall = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-]*/([a-zA-Z0-9_\-]+)\.git", src)
    if findall:
        repo_name: str = findall[0]
        if not name:
            if repo_name.startswith("bot_"):
                name = repo_name
            else:
                name = input("请输入插件名：")
                if not name:
                    echo("????")
                    return

        name = strip_plugin_name(name)

        echo(f"正在安装插件 [{name}]")
        if check_plugin_exists(name):
            echo(f"插件 [{name}] 已存在")
            return
        try:
            subprocess.run(
                [*git_cmd(), src, str(PLUGIN_DIR / f"bot_{name}")]
            ).check_returncode()
        except Exception as e:
            echo(f"插件 [{name}] 安装失败, error: {e}")
        else:
            echo(f"插件 [{name}] 安装成功")
            data[name] = src
        return

    # 路径链接，可能是文件夹，可能是文件
    # 文件
    # https://github.com/opq-osc/botoy-plugins/blob/master/plugins/bot_TaoShow.py
    if "/blob/" in src:
        raw_url = src.replace("/blob/", "/raw/")
        filename = src.split("/")[-1]
        if not filename.startswith("bot_"):
            name = input("请输入插件名：")
            if not name:
                echo("????")
                return
        else:
            name = filename
        if name.endswith(".py"):
            name = name[:-3]
        name = strip_plugin_name(name)
        echo(f"正在安装插件 [{name}]")
        if check_plugin_exists(name):
            echo(f"插件 [{name}] 已存在")
            return
        plugin_file = PLUGIN_DIR / f"bot_{name}.py"
        echo(f"正在下载文件 [{plugin_file}]")
        try:
            resp = httpx.get(raw_url, follow_redirects=True, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            echo(f"插件 [{name}] 安装失败, error: {e}")
        else:
            echo(f"插件 [{name}] 安装成功")
            plugin_file.write_bytes(resp.content)
            data[name] = src
        return

    # 文件夹
    # https://github.com/opq-osc/botoy-plugins/tree/master/plugins/bot_weirdfonts
    if "/tree/" in src:
        try:
            owner: str
            repo: str
            owner, repo = re.findall(
                r"github\.com/([a-zA-Z0-9][a-zA-Z0-9\-]*)/([a-zA-Z0-9_\-]+)", src
            )[0]
        except Exception:
            echo("链接有误，无法匹配到用户名和仓库名")
            return

        branches = [
            i["name"]
            for i in httpx.get(
                f"https://api.github.com/repos/{owner}/{repo}/branches", timeout=20
            ).json()
        ]
        for branch in branches:
            if f"/tree/{branch}/" in src:
                break
        else:
            echo("程序错误，无法确定分支名称")
            return

        path = re.findall(f"/tree/{branch}/(.*)", src)  # type: ignore
        if not path:
            echo("程序错误，无法处理路径")
            return
        path: str = path[0].strip("/")

        dir_name = path.split("/")[-1]
        if not dir_name.startswith("bot_"):
            name = input("请输入插件名：")
            if not name:
                echo("????")
                return
        else:
            name = dir_name
        name = strip_plugin_name(name)
        echo(f"正在安装插件 [{name}]")
        if check_plugin_exists(name):
            echo(f"插件 [{name}] 已存在")
            return
        path_dir = PLUGIN_DIR / f"bot_{name}"
        path_dir.mkdir()
        try:
            tree_data = httpx.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
                timeout=20,
            ).json()
            tree = tree_data["tree"]
            for node in tree:
                if node["path"] != path and node["path"].startswith(path):
                    if node["type"] != "blob":
                        raise RuntimeError("文件夹下载不支持嵌套文件夹，请手动安装此插件")
                    filename = node["path"].split("/")[-1]
                    echo(f"正在下载文件 [{node['path']}]")
                    base64_str = httpx.get(node["url"], timeout=20).json()["content"]
                    (path_dir / filename).write_bytes(base64.b64decode(base64_str))
        except Exception as e:
            echo(f"插件 [{name}] 安装失败, error: {e}")
            echo(f"正在移除目录 [{path_dir}]")
            shutil.rmtree(path_dir)
        else:
            echo(f"插件 [{name}] 安装成功")
            data[name] = src
        return

    echo("请查看帮助输入有效参数！")


@plugin.command()
@click.argument("src", required=False)
@click.argument("name", required=False)
def install(src: Optional[str] = None, name: Optional[str] = None):
    """安装插件 install [src] [name]

    src 为插件地址

    1. 可以为 github仓库克隆链接，注意一定要以.git结尾

    2. 可以为 github目录链接，点击文件夹或文件后浏览器地址栏中的地址
    当链接为目录链接也就是文件夹链接时，该文件夹下不能有子文件夹

    name 为插件名，不应该加bot_前缀

    src和name都是可选的，当src未传时将安装plugins.json中未被安装的插件
    """
    if not PLUGIN_DIR.exists():
        echo("plugins 文件夹不存在！")
        exit(1)
    try:
        plugin_data = json.loads(Path("plugins.json").read_text())
    except FileNotFoundError:
        echo("plugins.json 不存在!")
        plugin_data = {}

    if not src and not plugin_data:
        exit(echo("plugins数据为空，请提供足够的参数"))

    if src:
        install_plugin(src, name, plugin_data)
    else:
        for name, src in plugin_data.items():
            install_plugin(src, name, plugin_data)  # type: ignore

    Path("plugins.json").write_text(
        json.dumps(plugin_data, ensure_ascii=False, indent=2)
    )


@plugin.command()
@click.argument("names", nargs=-1, required=False)
def remove(names: Optional[List[str]] = None):
    """移除插件，也就是删除目录，可以同时删除多个插件，插件之间以空格分割"""
    if not PLUGIN_DIR.exists():
        echo("plugins 文件夹不存在！")
        exit(1)

    try:
        plugin_data = json.loads(Path("plugins.json").read_text())
    except FileNotFoundError:
        plugin_data = {}

    names = names or shlex.split(input("请输入插件名空格分割："))
    names = [name.strip().strip(".py") for name in names]
    for name in names:
        if name.startswith("bot_"):
            name = name[4:]
        if not name:
            continue

        path_dir = PLUGIN_DIR / f"bot_{name}"
        path_file = PLUGIN_DIR / f"bot_{name}.py"
        path = path_dir.exists() and path_dir or path_file
        if path.exists():
            if click.confirm(f"是否删除 [{path.absolute()}]"):
                if path.is_file():
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                if name in plugin_data:
                    del plugin_data[name]
            else:
                echo(f"取消删除 [{path.absolute()}]")
        else:
            echo(f"插件[{name}]不存在！")

    Path("plugins.json").write_text(
        json.dumps(plugin_data, ensure_ascii=False, indent=2)
    )


@plugin.command()
def list():
    """列出当前插件目录下所有的插件名"""
    if not PLUGIN_DIR.exists():
        echo("plugins 文件夹不存在！")
        exit(1)

    names = []
    for item in PLUGIN_DIR.iterdir():
        name = item.name
        if not name.startswith("bot_"):
            continue
        if item.is_dir():
            names.append(name[4:])
        elif item.is_file() and name.endswith(".py"):
            names.append(name[4:-3])

    try:
        plugin_data = json.loads(Path("plugins.json").read_text())
    except FileNotFoundError:
        plugin_data = {}

    for idx, name in enumerate(names):
        if name in plugin_data:
            names[idx] = f"{name} \t=> {plugin_data[name]}"
        else:
            names[idx] = f"{name} \t=> 该插件未记录在plugins.json中"

    echo(names and "\n".join(names) or "没有插件！")


if __name__ == "__main__":
    plugin()
