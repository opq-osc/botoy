import io

from setuptools import find_packages, setup

meta = {}

with io.open("./botoy/__version__.py", encoding="utf-8") as f:
    exec(f.read(), meta)  # pylint: disable=W0122


def read_files(files):
    data = []
    for file in files:
        with io.open(file, encoding="utf-8") as f:
            data.append(f.read())
    return "\n".join(data)


setup(
    name="botoy",
    description="OPQBot/IOTQQ/IOTBot的Python开发助手",
    long_description=read_files(["README.md", "CHANGELOG.md"]),
    long_description_content_type="text/markdown",
    version=meta["__version__"],
    author="wongxy",
    author_email="xiyao.wong@foxmail.com",
    url="https://github.com/xiyaowong/botoy",
    license="MIT",
    keywords=["iotbot", "iotqq", "OPQ", "OPQBot"],
    packages=find_packages(),
    install_requires=read_files(["requirements.txt"]),
    entry_points="""
        [console_scripts]
        botoy=botoy.cli:cli
    """,
    python_requires=">=3.7",
)
