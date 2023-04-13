import asyncio
import importlib
import json
import os
import pathlib
import sys
import textwrap
from typing import List

import click

from ..__version__ import __version__, check_version
from ..async_client import AsyncBotoy
from ..client import Botoy
from ..config import jconfig
from ..runner import run as run_with_reload
from ..utils import check_schema
from .plugin import plugin

echo = click.echo


def getchar(msg: str = "", choices: List[str] = [], echo: bool = False):
    if msg:
        print(msg + " ", end="", flush=True)
    while True:
        char = click.getchar(echo)
        if not choices or char in choices:
            print("")
            return char


@click.group()
def cli():
    """botoy 脚手架

    使用示例:

    1. 生成主体文件
    $ botoy init

    生成主体文件, 文件名为bot, qq号为123456:
    $ botoy init -n bot -q 123456

    2. 生成插件
    $ botoy add

    生成插件，名为test
    $ botoy add -n test

    生成插件，名为test, 只需要处理好友消息
    $ botoy add -n test -f

    生成插件，名为test, 需要处理好友消息, 群消息
    $ botoy add -n test -f -g

    可选项为-f -g -e 分别代表是否包含处理好友，群，事件，如果都不传，表示都要！

    3. 启动机器人(要求入口文件名为bot.py)
    $ botoy run

    4. 测试连接
    $ botoy test http://127.0.0.1:8888
    """


@cli.command()
def version():
    """版本号"""
    echo(__version__)
    check_version(False)


@cli.command()
@click.option("-n", "--name", prompt="程序入口文件名", default="bot", show_default=True)
@click.option(
    "-q", "--qq", prompt="机器人qq号", type=int, required=True, default=0, show_default=True
)
@click.option(
    "--host", prompt="机器人运行host", default="http://127.0.0.1", show_default=True
)
@click.option("--port", prompt="机器人运行端口", default=8888, show_default=True, type=int)
def init(name, qq, host, port):
    """创建程序入口文件和配置文件"""
    plug = click.confirm("是否使用插件功能", default=True, show_default=True)
    template = (
        textwrap.dedent(
            """
        from botoy import Action, Botoy, EventMsg, FriendMsg, GroupMsg
        from botoy import decorators as deco

        qq = {qq}
        bot = Botoy(qq=qq, use_plugins={use_plugins})
        action = Action(qq)


        @bot.on_friend_msg
        @deco.ignore_botself
        def friend(ctx: FriendMsg):
            if ctx.Content == 'test':
                action.sendFriendText(ctx.FromUin, 'ok')


        @bot.on_group_msg
        @deco.ignore_botself
        def group(ctx: GroupMsg):
            if ctx.Content == 'test':
                action.sendGroupText(ctx.FromGroupId, 'ok')


        @bot.on_event
        def event(ctx: EventMsg):
            pass


        if __name__ == "__main__":
            bot.run()
    """
        )
        .format(qq=qq, use_plugins=plug)
        .strip()
    )

    # main
    confirm = click.confirm(
        f"将生成 程序入口文件{name}.py 和 配置文件botoy.json, 这是覆盖写操作，是否继续?",
        default=False,
        show_default=True,
    )
    if not confirm:
        echo("操作已取消")
        sys.exit()

    with open(f"{name}.py", "w", encoding="utf8") as f:
        f.write(template)
    echo(f"已生成{name}.py")
    echo(
        f"""
    运行如下命令:
        python {name}.py
    然后给机器人或机器人所在的群发送 test 不出意外，机器人会回复 ok!
    """
    )
    # config file
    config = {
        "host": check_schema(host),
        "port": port,
        "group_blacklist": [],
        "friend_blacklist": [],
        "blocked_users": [],
        "webhook": False,
        "webhook_post_url": "http://127.0.0.1:5000",
        "webhook_timeout": 20,
    }
    with open("botoy.json", "w", encoding="utf8") as f:
        json.dump(config, f, indent="  ")

    if plug:
        if not os.path.isdir("plugins"):
            os.makedirs("plugins")

    if click.confirm("是否修改或生成.gitignore文件", default=False, show_default=True):
        ignore = "\n".join(
            ["\n# Botoy", "botoy.json", "REMOVED_PLUGINS", "botoy-cache"]
        )
        with open(".gitignore", "a" if os.path.exists(".gitignore") else "w") as f:
            f.write(ignore)


@cli.command()
@click.option("-n", "--name", prompt="插件名", required=True)
@click.option("-f", "--friend", is_flag=True, help="是否要接收好友消息?")
@click.option("-g", "--group", is_flag=True, help="是否要接收群消息?")
@click.option("-e", "--event", is_flag=True, help="是否要接收事件消息?")
def add(name, friend, group, event):
    """创建插件"""
    here = pathlib.Path(".").absolute()
    if here.name != "plugins":
        plugin_dir = here / "plugins"
        if not os.path.isdir("plugins"):
            plugin_dir.mkdir()
            echo("插件目录plugins不存在, 已自动创建")
    else:
        plugin_dir = here

    plugin_path_file = plugin_dir / f"bot_{name}.py"
    plugin_path_folder = plugin_dir / f"bot_{name}"
    if plugin_path_file.exists() or plugin_path_folder.exists():
        sys.exit("该插件名已被使用，请换一个插件名")
    if not any([friend, group, event]):
        friend = group = event = True

    imports = ["Action"]
    receivers = []
    if friend:
        imports.append("FriendMsg")
        receivers.append(
            textwrap.dedent(
                """
                @deco.ignore_botself
                def receive_friend_msg(ctx: FriendMsg):
                    Action(ctx.CurrentQQ)
                """
            )
        )
    if group:
        imports.append("GroupMsg")
        receivers.append(
            textwrap.dedent(
                """
                @deco.ignore_botself
                def receive_group_msg(ctx: GroupMsg):
                    Action(ctx.CurrentQQ)
                """
            )
        )
    if event:
        imports.append("EventMsg")
        receivers.append(
            textwrap.dedent(
                """
                def receive_events(ctx: EventMsg):
                    Action(ctx.CurrentQQ)
                """
            )
        )

    use_file = click.confirm(
        "插件使用单文件还是文件夹形式, 默认选是表示单文件(是表示单文件，否表示文件夹)", default=True, show_default=True
    )
    if use_file:
        write_file = plugin_path_file
    else:
        plugin_path_folder.mkdir()
        write_file = plugin_path_folder / "__init__.py"

    with open(write_file, "w", encoding="utf8") as f:
        f.write("from botoy import {}".format(", ".join(imports)))
        f.write("\nfrom botoy import decorators as deco")
        f.write("\n\n")
        f.write("\n".join(receivers))
    echo("ok")


@cli.command()
def run():
    """启动机器人
    要求入口文件名为bot.py
    """
    # look for bot.py
    if not pathlib.Path("bot.py").exists():
        sys.exit("该命令只接受入口文件命名为bot.py")
    # look for Botoy client
    sys.path.append(str(pathlib.Path(".").absolute()))
    module = importlib.import_module("bot")
    client = None
    for item in module.__dict__.values():
        if isinstance(item, (Botoy, AsyncBotoy)):
            client = item
            break
    else:
        sys.exit("无法找到(Async)Botoy对象")
    if client is not None:
        # 先判断子类
        if isinstance(client, AsyncBotoy):
            asyncio.run(client.run())
        else:
            client.run()


@cli.command()
def hot():
    """启动机器人, 同时开启自动重载
    要求入口文件名为bot.py
    """
    # look for bot.py
    if not pathlib.Path("bot.py").exists():
        sys.exit("该命令只接受入口文件命名为bot.py")
    # look for Botoy client
    sys.path.append(str(pathlib.Path(".").absolute()))
    module = importlib.import_module("bot")
    client = None
    for item in module.__dict__.values():
        if isinstance(item, (Botoy, AsyncBotoy)):
            client = item
            break
    else:
        sys.exit("无法找到(Async)Botoy对象")
    if client is not None:
        run_with_reload(client, True)


@cli.command()
@click.argument("address", required=False, default="http://127.0.0.1:8888")
def test(address: str):
    """测试连接
    可以加参数 test http://127.0.0.1:8888, 这也是默认值
    """

    items = address.split(":")
    items_count = len(items)
    if items_count == 3:  # http://host:port
        host = items[0] + ":" + items[1]
        port = items[2]
    elif items_count == 2:  # http://host, host:port
        if address.startswith("http"):
            host, port = address, 80
        else:
            host, port = items
    else:  # host
        host, port = address, 80

    Botoy(host=host, port=int(port)).run()


@cli.command()
def sweet():
    """快速启动

    该命令用于只需要插件功能的情况, 只会读取插件
    """

    def get_args():
        host = jconfig.host
        if getchar(f"需要更改host吗？当前为({host}) y/n", ["y", "n"]) == "y":
            host = input("Host: ")

        port = jconfig.port
        if getchar(f"需要更改port吗？当前为({port}) y/n", ["y", "n"]) == "y":
            port = int(input("Port: "))

        qq = None
        if getchar(f"需要设置机器人QQ号吗？(不建议设置，因为这里的qq只是筛选作用) y/n", ["y", "n"]) == "y":
            qq = int(input("QQ: "))

        is_async = getchar("使用异步吗?（建议使用）y/n", ["y", "n"]) == "y"

        log = getchar("是否开启控制台日志 y/n") == "y"

        if (
            getchar(
                f"当前设置为 Host: {host}, Port: {port}, QQ: {qq}, is_async: {is_async}, log: {log}, 是否需要重新设置？ y/n",
                ["y", "n"],
            )
            == "y"
        ):
            return get_args()
        return host, port, qq, is_async, log

    host, port, qq, is_async, log = get_args()
    if is_async:
        c = AsyncBotoy
    else:
        c = Botoy

    bot = c(qq=qq, host=host, port=port, use_plugins=True, log=log)
    if isinstance(bot, AsyncBotoy):
        asyncio.run(bot.run())
    else:
        bot.run()


cli.add_command(plugin)


if __name__ == "__main__":
    cli()
