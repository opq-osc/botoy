import asyncio
import itertools
import os
import subprocess
import sys
import textwrap
import time
from functools import lru_cache
from pathlib import Path
from typing import Union

import colorama

from .async_client import AsyncBotoy
from .client import Botoy


@lru_cache(maxsize=2333)
def _get_running_args():
    main = sys.modules["__main__"]
    spec = getattr(main, "__spec__", None)
    if spec:
        return [sys.executable, "-m", spec.name] + sys.argv[1:]
    return [sys.executable] + sys.argv


def _restart_process():
    return subprocess.Popen(
        _get_running_args(),
        env={
            **os.environ,
            "BOTOY_CHILD": "true",
        },
    )


def _iter_module_files():
    for module in list(sys.modules.values()):
        if module is None:
            continue
        filename = getattr(module, "__file__", None)
        if filename:
            if filename[-4:] in (".pyc", ".pyo"):
                filename = filename[:-1]
            yield filename


def run(bot: Union[Botoy, AsyncBotoy], auto_reload: bool = False):
    """运行

    :param bot: bot实例
    :param auto_reload: 是否自动重载，当plugins目录内有文件或程序依赖的模块文件变动
    时将自动重启，部署时请勿开启该功能
    注意：只有修改操作才会进行重载，添加和删除文件不会
    """
    if auto_reload and os.getenv("BOTOY_CHILD") != "true":

        print(
            textwrap.dedent(
                f"""
              {colorama.Fore.RED}
              ***********************************
              *                                 *
              *  已开启自动重载，部署时请关闭!  *
              *                                 *
              ***********************************
              {colorama.Fore.RESET}"""
            ).strip()
        )

        process = _restart_process()
        try:
            mtimes = {}
            while True:
                need_restart = False

                for filename in itertools.chain(
                    _iter_module_files(), Path("plugins").glob("**/*")
                ):
                    filename = (
                        filename
                        if isinstance(filename, str)
                        else str(filename.absolute())
                    )
                    if "__pycache__" in filename or not os.path.isfile(filename):
                        continue
                    mtime = os.stat(filename).st_mtime
                    old_mtime = mtimes.get(filename)
                    if old_mtime is None:
                        mtimes[filename] = mtime
                        continue
                    elif mtime > old_mtime:
                        mtimes[filename] = mtime
                        need_restart = True
                        break

                if need_restart:
                    process.terminate()
                    process.wait()
                    process = _restart_process()
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            process.terminate()
            process.wait()

        return

    return asyncio.run(bot.run()) if isinstance(bot, AsyncBotoy) else bot.run()
