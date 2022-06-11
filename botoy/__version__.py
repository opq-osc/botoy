# pylint: disable=C0415,C0413
# type: ignore
__version__ = "8.3"


def check_version(daemon=True):
    def _check_version():
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

                try:
                    from rich.console import Console
                    from rich.markdown import Markdown

                    def mprint(msg):
                        Console().print(Markdown(msg))

                except Exception:
                    mprint = print

                info = f"\n\n\033[33m==== 当前版本为: \033[31m{local_version}\033[33m, 已有最新版本: \033[31m{latest_version}\033[33m, 请及时更新! ====\033[0m\n\n"

                try:
                    releases = httpx.get(
                        "https://api.github.com/repos/opq-osc/botoy/releases",
                        timeout=10,
                    ).json()
                    needed_releases = []
                    for release in releases:
                        if V(release["tag_name"][1:]) > local_version:
                            needed_releases.append(release)

                    tips = []
                    for release in needed_releases:
                        tips.append(f"**{release['tag_name']}**\n{release['body']}\n")

                    info += "\n".join(tips)
                except Exception:
                    pass

                mprint(info)

    from threading import Thread

    t = Thread(target=_check_version)
    t.setDaemon(daemon)
    t.start()
