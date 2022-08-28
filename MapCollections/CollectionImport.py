import asyncio
import os
import pickle
import re

from retrying import retry
from loguru import logger
from rich import print
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table

from packages.osuApiV2 import AsyncLoginClient
from packages.osuDirs import osuDirGet as dirOsu
from packages.osuDirs import songsDir as dirSongs
from packages.osu_db.collections_db import collection_write_one
from packages.osu_db.osu_db import read_osu_db
from packages.sayobotApi import AsyncSayobot

illegal_chars = re.compile(r"[\<\>:\"\/\\\|\?*]")


def detect_if_non():
    if not os.path.isdir("collections_import"):
        print('[red]现在还没有任何一个可以导入的收藏夹文件，已经在程序根目录创建了collections_import文件夹。'
              '[red]把colldb文件塞进去再打开一次就可以了')
        print('[red]colldb文件可以让别人通过另一个导出工具进行导出，当然你自己也行，但那没有意义')
        print('[red]按下回车退出...')
        print("===========================================================")
        print('[red]You have no coll db yet. The "collections_import" dir is created. '
              '[red]Please put the colldb file into it')
        print('[red]The colldb file can be export by others or export by yourself.')
        print('[red]Press Enter to exit...')
        os.mkdir("collections_import")
        input()
        exit(1919810)

    all_files = []
    for root, dirs, files in os.walk("collections_import"):
        for f in files:
            all_files.append(f)

    if not all_files:
        print('[red]现在还没有任何一个可以导入的收藏夹文件。'
              '[red]把colldb文件塞进collections_import文件夹再打开一次就可以了')
        print('[red]colldb文件可以让别人通过另一个导出工具进行导出，当然你自己也行，但那没有意义')
        print('[red]按下回车退出...')
        print("===========================================================")
        print('[red]You have no coll db yet. The "collections_import" dir is created. '
              '[red]Please put the colldb file into it')
        print('[red]The colldb file can be export by others or export by yourself.')
        print('[red]Press Enter to exit...')
        os.mkdir("collections_import")
        input()
        exit(1919810)

    now_dir = os.getcwd()
    return [os.path.join(now_dir, "collections_import", file) for file in all_files]


def read_all_db_files(all_files: list) -> dict:
    coll_dict = {}
    for file in all_files:
        file_content = pickle.load(open(file, 'rb'))
        coll_dict[f"{file_content['coll_name']} by {file_content['user_name']}"] = file_content

    return coll_dict


def ask_for_import(collections: dict) -> list:
    print("===========================================================")
    print("下面是你所有可以导入的收藏夹")
    print("Here's all collections you can import.")
    print("===========================================================")

    correspond = {}
    n = 0
    for key, value in collections.items():
        print(f"{n}. {key} ({value['size']})")
        correspond[n] = key
        n += 1
    del n

    print("===========================================================")
    print("[yellow]如果想导入多个的话，输入多个序号并在序号间添加英文半角逗号")
    print("[yellow]If you wanna import more than one, input numbers that split with ',' (Dont input space)")
    selection = input("Which do you want to import: ")

    if "," in selection:
        selection = selection.split(',')
    else:
        selection = [selection]

    result = []
    for s in selection:
        s = int(s)
        result.append(correspond[s])

    return result


def organize_information(collections: dict, selection: list) -> dict:
    map_to_download_info = []
    for s in selection:
        for beatmap in collections[s]['beatmaps']:
            map_to_download_info.append(beatmap)

    try:
        osu_db_data = read_osu_db(os.path.join(dirOsu(), 'osu!.db'))
        all_sid_exists = [beatmap['beatmap_set_id'] for beatmap in osu_db_data['beatmaps']]
    except FileNotFoundError:
        all_sid_exists = []

    map_to_exclude = []
    for beatmap in map_to_download_info:
        if beatmap['beatmap_set_id'] in all_sid_exists:
            map_to_exclude.append(beatmap)
    for beatmap in map_to_exclude:
        map_to_download_info.remove(beatmap)
    del map_to_exclude

    map_to_download = {}
    for beatmap in map_to_download_info:
        map_to_download[beatmap['beatmap_set_id']] = beatmap
    del map_to_download_info

    return map_to_download


def ask_mirror():
    print("===========================================================")
    print("[green]选择要使用的下载源")
    print("[green]Select download mirror.")
    print("")
    print("如果你在中国大陆，那么我推荐使用小夜镜像源。相反则使用官方镜像源。当然视你的具体情况而定。")
    print("If you r in China mainland, I suggest to use sayobot. On the contrary use official. "
          "Consider your real condition.")
    print("===========================================================")
    print("0. 官方 (official)\n"
          "1. 小夜 (sayobot)\n")
    mirror = int(input("Which is your selection: "))
    if mirror == 0:
        mirror = 'official'
    elif mirror == 1:
        mirror = 'sayobot'
    else:
        print("[red]Error: please input correct num.")
        exit(911)

    return mirror


def ask_sem() -> int:
    print("===========================================================")
    print("[green]输入下载时同时进行的最大任务数")
    print("[green]Input the number of downloading at the same time.")
    print("")
    print("官方镜像源建议为5(API限制)。小夜无所谓，但最好不要超过20，考虑你的实际网络。")
    print(
        "Its 5 suggested in official (api restricted). And any in sayobot. When in sayobot, its suggests that 20 at most. "
        "Consider your real condition.")
    print("===========================================================")
    return int(input("Input: "))


async def map_download(maps_to_download: dict, mirror: str, sem: int):
    def download_progress_define(total_count):
        """
        定义了下载进度的样式
        """
        download_progress = Progress(
            "{task.description}",
            # 添加的效果从左到右排列
            # 添加效果，六个点转圈(类似右边的符号): ⠋ ⠹ ⠴
            SpinnerColumn(),
            # 添加效果，条状的进度条
            BarColumn(),
            # 添加效果，百分比进度显示  [progress.percentage]是颜色紫色(默认)  {task.percentage:>3.0f}是格式化，rich自带的
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            transient=True
        )
        # 总的进度类
        total_progress = Progress(
            "{task.description}",
            # 添加的效果从左到右排列
            # 添加效果，六个点转圈(类似右边的符号): ⠋ ⠹ ⠴
            SpinnerColumn(),
            # 添加效果，条状的进度条
            BarColumn(),
            # 添加效果，百分比进度显示  [progress.percentage]是颜色紫色(默认)  {task.percentage:>3.0f}是格式化，rich自带的
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )

        total_task = total_progress.add_task('[yellow]Total', total=total_count)

        progress_table = Table.grid()

        progress_table.add_row(
            Panel.fit(
                total_progress,
                title="总下载进度",
                border_style="red",
                padding=(0, 2)
            )
        )
        progress_table.add_row(
            Panel.fit(
                download_progress,
                title="分下载进度",
                border_style="green",
                padding=(0, 2)
            )
        )
        return download_progress, total_progress, progress_table, total_task

    # download_progress total_progress 是分下载进度和总下载进度的样式，一样的只不过分下载进度完成后会消失
    # progress_table 是总的布局框 里边存放两大块下载进度的显示(一总一分)
    # total_task 是总的下载进度
    download_progress, total_progress, progress_table, total_task = download_progress_define(len(maps_to_download))

    if mirror == "official":
        print("===========================================================")
        client = AsyncLoginClient()
        username = input("输入osu的用户名(官方下载需要这个)\n"
                         "Input your OSU username (Official download needed): ")
        password = input("输入osu的密码\n"
                         "Input your OSU password: ")
        print("===========================================================")
        print("尝试登录osu...\n"
              "Try login osu...")
        await client.login(username, password)
        print("[green]登录成功\n"
              "[green]Login successfully.")
    elif mirror == 'sayobot':
        client = AsyncSayobot()
    else:
        client = 0
        print("[red]Error, report it as a issue on github.")

    print("[yellow]10秒后开始下载铺面并添加新收藏夹，之后只需等待，但不要玩osu，自动刷新的铺面列表会让没下载完的铺面无法导入\n"
          "[yellow]Will download maps in 10 seconds. You can go and do something expect playing osu. "
          "The auto map refresh will crash the map in downloading and will import failed.")
    await asyncio.sleep(10)

    @retry()
    async def single_download(download_progress, total_progress, client, beatmapset, songs_dir, sem):
        """
        定义了单个铺面下载时的函数
        """
        # 并发设置
        async with sem:
            n = 0
            # 开始下载循环
            async for i in client.download_beatmapset(
                    beatmapset['id'],
                    f"{songs_dir}{beatmapset['id']} {illegal_chars.sub('_', beatmapset['artist'])} - {illegal_chars.sub('_', beatmapset['title'])}.osz"
            ):
                if n == 0:
                    download_job = download_progress.add_task(f'[green]{beatmapset["id"]}', total=i)
                if n != 0:
                    download_progress.advance(download_job)
                n += 1
            # 总任务进度 +1
            total_progress.advance(total_task)
            for task in download_progress.tasks:
                # 完成的任务就让它的进度条消失
                if task.finished:
                    task.visible = False

    # 设置并发
    sem = asyncio.Semaphore(sem)
    # 获取songs的目录
    songs_dir = dirSongs()

    # 设置并发任务
    tasks = []
    for sid, map_detail in maps_to_download.items():
        beatmap = {
            'id': sid,
            'artist': map_detail['artist'],
            'title': map_detail['song_title']
        }

        tasks.append(
            single_download(
                download_progress=download_progress,
                total_progress=total_progress,
                client=client,
                beatmapset=beatmap,
                songs_dir=songs_dir,
                sem=sem
            )
        )

    # 使用动态进度显示
    with Live(progress_table, refresh_per_second=10, transient=True):
        # 开始任务
        await asyncio.gather(*tasks)


def write_collection(collections: dict, selection: list):
    collection_dir = os.path.join(dirOsu(), "collection.db")
    for s in selection:
        coll = collections[s]
        print(f"Writing {coll['coll_name']} from {coll['user_name']}")
        collection_write_one(
            collection_dir,
            f"{coll['coll_name']} by {coll['user_name']}",
            [beatmap['md5_hash'] for beatmap in coll['beatmaps']]
        )


async def main():
    print("[yellow]在使用之前，请确保已经关闭了osu，任何对数据库或者铺面的改动都可能导致某些问题\n"
          "[yellow]Before use this tool. Please make sure that have shut down OSU. "
          "Any modification to db file or beatmaps may cause some exceptions.")
    # 检测有没有可以导入的文件
    all_coll_db_files = detect_if_non()
    # 读取所有文件
    collections: dict = read_all_db_files(all_coll_db_files)
    # 询问并返回要导入的选择
    selection = ask_for_import(collections)
    # 整合要下载的铺面信息
    maps_to_download: dict = organize_information(collections, selection)
    # 询问镜像站的选择
    print(f"一共需要下载{len(maps_to_download)}张铺面")
    print(f"Need to download {len(maps_to_download)} new beatmaps.")
    mirror: str = ask_mirror()
    # 询问下载的并发数
    sem: int = ask_sem()
    # 下载铺面
    await map_download(maps_to_download, mirror, sem)
    # 写入收藏夹
    write_collection(collections, selection)

    print("[green]按下回车退出...\n"
          "[green]Press Enter to exit")
    input()


if __name__ == '__main__':
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except Exception as e:
        logger.exception(e)
