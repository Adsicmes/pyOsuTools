import asyncio
import json
import os
import pickle
import re

from rich import print

from packages.osuDirs import osuDirGet as dirOsu
from packages.osuDirs import songsDir as dirSongs
from packages.osu_db.collections_db import collection_read
from packages.osu_db.osu_db import read_osu_db


async def main():
    osu_dir_root = dirOsu()
    osu_dir_songs = dirSongs()
    osu_dir_collection = os.path.join(osu_dir_root, "collection.db")
    osu_dir_osu_db = os.path.join(osu_dir_root, "osu!.db")

    collections = collection_read(osu_dir_collection)
    osu_db = read_osu_db(osu_dir_osu_db)
    print(
        f"[green]===========================================================\n"
        f"[green]Your name: {osu_db['name']}\n"
        f"[green]osu!.db Version: {osu_db['version']}\n"
        f"[green]Beatmapsets count: {osu_db['folder_count']}\n"
        f"[green]Beatmaps num: {osu_db['num_beatmaps']}\n"
        f"[green]===========================================================\n"
        f"[green]collection.db Version: {collections['version']}\n"
        f"[green]Collection num: {collections['num_collections']}\n"
        f"[green]===========================================================\n"
        f"[yellow]没有问题的话按下回车继续...\n"
        f"[yellow]If theres no wrong. Press Enter to continue..."
    )
    input()

    print("以下是你的所有收藏夹，输入前边的标号并按下回车来导出")
    print("Here is all your collections, input the serial number to export...")
    print("===========================================================")

    n = 0
    for c in collections['collections']:
        print(f"{n}. {c['name']} ({c['size']})")
        n += 1

    print("===========================================================")
    print("[yellow]如果想导出多个收藏夹，用逗号来分割那些序号(不要乱加空格)")
    print("[yellow]If you want to export more than one, use ',' to split the number.(Dont input space.)")
    selection = input("Which to export: ")

    if ',' in selection:
        selection = selection.split(",")
    else:
        selection = [selection]

    if not os.path.isdir("collections_export"):
        os.mkdir("collections_export")

    illegal_chars = re.compile(r"[\<\>:\"\/\\\|\?*]")

    for s in selection:
        coll_raw = collections['collections'][int(s)]

        coll = {
            'user_name': osu_db['name'],
            'coll_name': illegal_chars.sub('_', coll_raw['name']),
            'size': coll_raw['size'],
            'beatmaps': []
        }

        for h in coll_raw['hashes']:
            for beatmap in osu_db['beatmaps']:
                if h == beatmap['md5_hash']:
                    coll['beatmaps'].append(beatmap)

        pickle.dump(coll, open(f"collections_export/{osu_db['name']} - {coll['coll_name']}.colldb", 'wb'))

    print("[green]导出到了collections_export文件夹，按下回车退出...")
    print("[green]Please check the collections_export folder.Press enter to exit...")
    input()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
