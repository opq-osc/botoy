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
    name="botoy_mutilhelper",
    description="基于botoy写的多QAPI",
    long_description=read_files(["README.md", "CHANGELOG.md"]),
    long_description_content_type="text/markdown",
    version=meta["__version__"],
    author="HeiLAAS",
    author_email="heng809156@gmail.com",
    url="https://github.com/HeiLAAS/botoy",
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
