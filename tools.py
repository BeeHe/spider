# coding: utf8


def compare(old=None, new=None):
    x = []
    if isinstance(old, list) and isinstance(new, list):
        for i in new:
            if i not in old:
                x.append(i)
    return x
