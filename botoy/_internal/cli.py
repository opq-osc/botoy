from typing import List

import click

echo = click.echo


def getchar(msg: str = "", choices: List[str] = [], echo: bool = False):
    if msg:
        print(msg + " ", end="", flush=True)
    while True:
        char = click.getchar(echo)
        if not choices or char in choices:
            print("")
            return char


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli():
    """botoy 脚手架

    botoy --help
    botoy go --help
    """


@cli.command()
@click.option("-p", "--plugin", is_flag=True, help="是否加载插件")
@click.option("-u", "--url", help="连接地址, 默认读取botoy.json中的url字段或者localhost:8086")
@click.option("-r", "--reload", is_flag=True, help="是否开启热重载")
def go(plugin, url, reload):
    """一键启动默认bot"""
    from botoy import bot

    if plugin:
        bot.load_plugins()
        bot.print_receivers()
    if url:
        bot.set_url(url)
    bot.run(reload)
