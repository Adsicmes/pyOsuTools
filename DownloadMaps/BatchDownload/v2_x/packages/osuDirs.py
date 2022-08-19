# import pywintypes
# import win32api
#
# 必须如上这么导入，否则会报错
# 即使ide显示为错误，实际运行不会出错
# 仅python3.8下如此，其他版本暂未测试
# 3.10可直接导入win32api无需导入pywintypes

import pywintypes
import win32api
import win32con
from getpass import getuser


def osuDirGet() -> str:
    """
    通过注册表获取osu的目录
    最后结尾为双右斜杠\\
    :return: osu目录
    """
    key = win32api.RegOpenKey(win32con.HKEY_CLASSES_ROOT,
                              'osu\\DefaultIcon', 0, win32con.KEY_READ)
    osu = win32api.RegQueryValue(key, '')
    osu = str(osu).split("\"")[1].split("\\")
    del osu[-1]
    dir = ''
    for i in osu:
        dir = dir + i + '\\'

    return dir


def songsDir() -> str:
    """
    以双右斜杠为结尾\\
    获取osu的Songs文件夹
    :return: Songs文件夹目录
    """
    dir = osuDirGet()
    config = dir + 'osu!.' + getuser() + '.cfg'

    with open(config, encoding='utf-8', errors='ignore') as f:
        content = f.readlines()

    n = 0
    for i in content:
        if 'BeatmapDirectory' in i:
            break
        else:
            n += 1
    content = content[n].replace("\n", "").split(' = ')

    if ':\\' not in content[1]:
        dir = dir + content[1]
    else:
        dir = content[1]

    return dir + '\\'


if __name__ == '__main__':
    print(songsDir())
