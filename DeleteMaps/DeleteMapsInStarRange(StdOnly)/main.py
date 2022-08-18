import oppadc
import shutil
import os

from json import dump as json_dump
from time import sleep


if __name__ == '__main__':
    print("在获取的过程中可以随时关闭窗口，不影响文件，删除堆在最后了")
    osu_dir = input("输入osu的目录: ")

    lowest_star = input("输入要删除的最低星数, 默认0: ")
    try:
        lowest_star = float(lowest_star)
    except ValueError:
        print("输入有误，删除的最低星数改为0")
        lowest_star = 0.0

    highest_star = input("输入要删除的最高星数, 默认0: ")
    try:
        highest_star = float(highest_star)
    except ValueError:
        print("输入有误，删除的最高星数改为0")
        highest_star = 0.0

    if lowest_star == highest_star:
        print("要删除的最低最高星数相等，退出程序")
        exit(1145141919810)
    if lowest_star > highest_star:
        print("要删除的最低星数大于最高星数，退出程序")
        exit(1145141919810)

    songs_dir = os.path.join(osu_dir, "Songs")
    print(f"获取Songs目录，{songs_dir}")

    songs_ = os.listdir(songs_dir)  # 获取songs目录下所有的文件和文件夹
    songs = [os.path.join(songs_dir, i) for i in songs_]  # 加入到列表
    print(f"获取到Songs目录下的所有文件夹，共{len(songs)}个")

    print("开始对所有文件夹进行遍历扫描，获取所有的.osu文件路径")
    sleep(1)

    # 初始化一个fail list，把下面所有的错加进去
    failed_list = []

    all_osu_maps_path = []

    for map_sets_dir in songs:
        # 如果不是文件夹，过
        if not os.path.isdir(map_sets_dir):
            continue

        dir_cons = os.listdir(map_sets_dir)
        count = 0
        # 遍历每个set的文件
        for file in dir_cons:
            # 是.osu文件就加入列表
            if file.endswith(".osu"):
                all_osu_maps_path.append(os.path.join(map_sets_dir, file))
                count += 1
        print(f"该目录加入了{count}个文件: {map_sets_dir}")

    print(f"开始检测{len(all_osu_maps_path)}张铺面的难度，筛选要删除的铺面")
    sleep(1)

    all_osu_maps_to_delete_path = []

    for osu_map in all_osu_maps_path:
        try:
            # 创建OsuMap对象
            this_map = oppadc.OsuMap(osu_map)
            # 获取star
            this_map_star = this_map.getStats(recalculate=True)
            print(f"{this_map_star.total}* -- {osu_map}")
            # 若符合删图的筛选范围，就加入
            if this_map_star.total < highest_star:
                if this_map_star.total > lowest_star:
                    all_osu_maps_to_delete_path.append(osu_map)
                    print(f"添加到删除列表: {osu_map}")
        except Exception as e:
            failed_list.append({"path": osu_map, "reason": "解析失败，大概率是别的模式的图",
                                "type": "file", "from": "oppadc.OsuMap"})

    print(f"开始删除{len(all_osu_maps_to_delete_path)}张铺面和osu!.db，该过程开始后尽量不要直接退出")
    sleep(3)
    print(f"删除osu!.db")
    osu_db_is_del = False
    try:
        os.remove(os.path.join(osu_dir, 'osu!.db'))
        osu_db_is_del = True
    except Exception as e:
        failed_list.append({"path": os.path.join(osu_dir, 'osu!.db'),
                            "reason": str(e), "type": "file", "from": "os.remove"})
        print("删除osu!.db失败")

    print("开始删除铺面")
    sleep(1)
    # 开始删除
    for osu_map in all_osu_maps_to_delete_path:
        try:
            if os.path.exists(osu_map):
                print(f"已删除 {osu_map}")
                os.remove(osu_map)
        except Exception as e:
            print(f"删除失败 {osu_map}")
            failed_list.append({"path": osu_map, "reason": e, "type": "file", "from": "os.remove"})

    # 定义出错函数给下方rmtree使用
    def on_shutil_rmtree_error(func, path, exc_info):
        print(f"删除失败 {path}")
        failed_list.append({"path": path, "reason": "删除目录失败", "type": "dir", "from": "shutil.rmtree"})

    print("开始检测目录是否含有.osu文件，作残余清理")
    sleep(1)
    # 重新遍历一遍，删除没有.osu文件的文件夹
    for map_sets_dir in songs:
        # 如果不是文件夹，过
        if not os.path.isdir(map_sets_dir):
            continue

        # 遍历内部的file，检测是不是有.osu
        dir_cons = os.listdir(map_sets_dir)
        is_break = False
        # 如果有.osu，就打断循环，设置为True
        for file in dir_cons:
            if file.endswith(".osu"):
                is_break = True
                break
        # 如果不是被打断的，也就是没有.osu，尝试删除
        if not is_break:
            print(f"不含.osu文件，尝试删除: {map_sets_dir}")
            shutil.rmtree(map_sets_dir, onerror=on_shutil_rmtree_error)

    json_temp = {"error": failed_list}

    if not osu_db_is_del:
        print("osu!.db删除失败，记得手动删除osu.db，错误正在记录到error.json，进里边对照着把所有删除失败的文件手动删掉，如果真的很多就是有bug")

    with open("error.json", "w") as fp:
        json_dump(json_temp, fp)
    print("保存报错成功")
    input("按回车退出...")










