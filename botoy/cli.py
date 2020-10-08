import json
import os
import pathlib
import sys
import textwrap

import click

from botoy.util import check_schema

echo = click.echo


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
    """


@cli.command()
@click.option('-n', '--name', prompt="程序入口文件名", default='bot', show_default=True)
@click.option('-q', '--qq', prompt="机器人qq号", type=int, required=True)
@click.option(
    '--host', prompt='机器人运行host', default='http://127.0.0.1', show_default=True
)
@click.option('--port', prompt='机器人运行端口', default=8888, show_default=True, type=int)
def init(name, qq, host, port):
    """创建程序入口文件和配置文件"""
    plug = click.confirm('是否使用插件功能', default=True, show_default=True)
    template = textwrap.dedent(
        """
        from botoy import Action, Botoy, EventMsg, FriendMsg, GroupMsg

        qq = {qq}
        bot = Botoy(qq=qq, use_plugins={use_plugins})
        action = Action(qq)


        @bot.on_friend_msg
        def friend(ctx: FriendMsg):
            if ctx.Content == 'test':
                action.sendFriendText(ctx.FromUin, 'ok')


        @bot.on_group_msg
        def group(ctx: GroupMsg):
            if ctx.Content == 'test':
                action.sendGroupText(ctx.FromGroupId, 'ok')


        @bot.on_event
        def event(ctx: EventMsg):
            pass


        if __name__ == "__main__":
            bot.run()
    """
    ).format(qq=qq, use_plugins=plug)

    # main
    confirm = click.confirm(
        f'将生成 程序入口文件{name}.py 和 配置文件botoy.json, 这是覆盖写操作，是否继续?',
        default=False,
        show_default=True,
    )
    if not confirm:
        echo('操作已取消')
        sys.exit()

    with open(f'{name}.py', 'w', encoding='utf8') as f:
        f.write(template)
    echo(f'已生成{name}.py')
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
    with open('botoy.json', 'w', encoding='utf8') as f:
        json.dump(config, f, indent='  ')

    if plug:
        if not os.path.isdir('plugins'):
            os.makedirs('plugins')


@cli.command()
@click.option('-n', '--name', prompt='插件名', required=True)
@click.option('-f', '--friend', is_flag=True, help='是否要接收好友消息?')
@click.option('-g', '--group', is_flag=True, help='是否要接收群消息?')
@click.option('-e', '--event', is_flag=True, help='是否要接收事件消息?')
def add(name, friend, group, event):
    """创建插件"""
    here = pathlib.Path('.').parent
    if here.name != 'plugins':
        if not os.path.isdir('plugins'):
            sys.exit('插件目录plugins不存在')
        plugin_dir = here / 'plugins'
    else:
        plugin_dir = here

    plugin_path = plugin_dir / f'bot_{name}.py'
    if os.path.exists(plugin_path):
        sys.exit('该插件已使用，请换一个插件名')
    if not any([friend, group, event]):
        friend = group = event = True

    imports = ['Action']
    receivers = []
    if friend:
        imports.append('FriendMsg')
        receivers.append(
            textwrap.dedent(
                """
                def receive_friend_msg(ctx: FriendMsg):
                    Action(ctx.CurrentQQ)
                """
            )
        )
    if group:
        imports.append('GroupMsg')
        receivers.append(
            textwrap.dedent(
                """
                def receive_group_msg(ctx: GroupMsg):
                    Action(ctx.CurrentQQ)
                """
            )
        )
    if event:
        imports.append('EventMsg')
        receivers.append(
            textwrap.dedent(
                """
                def receive_events(ctx: EventMsg):
                    Action(ctx.CurrentQQ)
                """
            )
        )
    with open(plugin_path, 'w', encoding='utf8') as f:
        f.write('from botoy import {}'.format(', '.join(imports)))
        f.write('\n\n')
        f.write('\n'.join(receivers))
    echo('ok')


if __name__ == "__main__":
    cli()
