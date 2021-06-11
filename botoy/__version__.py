# pylint: disable=C0415,C0413
__version__ = "6.2"


def check_version():
    def _check_version():
        import sys
        from distutils.version import LooseVersion as V
        from xml.etree import ElementTree

        import httpx

        try:
            latest_version = V(
                ElementTree.fromstring(
                    httpx.get(
                        "https://pypi.org/rss/project/botoy/releases.xml", timeout=10
                    ).text
                )
                .find("channel")
                .find("item")
                .find("title")
                .text
            )
        except Exception:
            pass
        else:
            local_version = V(__version__)
            if local_version < latest_version:
                info = f"\n\033[33m==== 当前版本为: \033[31m{local_version}\033[33m, 已有最新版本: \033[31m{latest_version}\033[33m, 请及时更新! ====\033[0m\n"
                sys.stdout.write(info)

    from threading import Thread

    t = Thread(target=_check_version)
    t.setDaemon(True)
    t.start()
