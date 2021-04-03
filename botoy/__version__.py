# pylint: disable=C0415,C0413
__version__ = '0.0.25'


def check_version():
    def _check_version():
        import re
        from distutils.version import LooseVersion as V

        import httpx

        try:
            resp = httpx.get(
                'https://mirrors.aliyun.com/pypi/simple/botoy/', timeout=10
            )
            resp.raise_for_status()
        except Exception:
            pass
        else:
            versions = re.findall(r'botoy-(.*?)\.tar\.gz', resp.text)
            if versions:
                versions = set(versions)
            local_v = V(__version__)
            latest_version = max(V(v) for v in versions)
            if local_v < latest_version:
                info = f'\033[33m==== 当前版本为: \033[31m{local_v}\033[33m, 已有最新版本: \033[31m{latest_version}\033[33m, 请及时更新! ====\033[0m'
                print(info)

    from threading import Thread

    t = Thread(target=_check_version)
    t.setDaemon(True)
    t.start()
