from typing import Optional

from botoy.exceptions import InvalidConfigError


def dict2tree(data: dict) -> dict:
    res = {}
    for key in data.keys():
        if "." not in key:
            res[key] = data[key]
        else:
            parts = key.split(".")
            pre = res
            count = len(parts)
            for idx, part in enumerate(parts):
                if idx == count - 1:
                    pre[part] = data[key]
                else:
                    try:
                        pre[part] = pre[part]
                    except KeyError:
                        pre[part] = {}
                    pre = pre[part]
                    if not isinstance(pre, dict):
                        raise InvalidConfigError(f'"{part}" 不能作为键名, 请查看文档修改你的配置')
    return res


def lookup(
    tree: dict,
    key: Optional[str] = None,
):
    if not key:
        return tree
    node = tree
    for part in key.split("."):
        node = node[part]
    return node


if __name__ == "__main__":
    tree = dict2tree(
        {
            "a.b.c": True,
            "a.b.d": True,
            "a.e.d": [],
        }
    )
    assert tree == {"a": {"b": {"c": True, "d": True}, "e": {"d": []}}}
    a_tree = lookup(tree, "a")
    assert a_tree == {"b": {"c": True, "d": True}, "e": {"d": []}}
    assert lookup(a_tree, "e.d") == []
