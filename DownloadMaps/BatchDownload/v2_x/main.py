import os
import json
import asyncio
import re

from retrying import retry

from rich import print
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table

from packages.osuDirs import osuDirGet, songsDir
from packages.osu_db.osu_db import read_osu_db
from packages.osuApiV2 import AsyncLoginClient


illegal_chars = re.compile(r"[\<\>:\"\/\\\|\?*]")


def get_sids_have_existed() -> list:
    """
    读取osu!.db  并排除重复项  得到目前osu内已经存在的铺面
    """
    osu_db_info = read_osu_db(osuDirGet() + 'osu!.db')
    sids_have_existed = list(set([beatmap['beatmap_set_id'] for beatmap in osu_db_info['beatmaps']]))
    return sids_have_existed


async def scrape_maps(params, sid_existed) -> list:
    """
    从ppy搜索铺面，采用ppy官方的搜索参数
    """
    is_break = False
    beatmap_list = []
    async with AsyncLoginClient() as login_client:
        login_client: AsyncLoginClient
        await login_client.login(
            params['api']['username'],
            params['api']['password']
        )
        # 组织搜索条件
        official = params['official']
        params_ = {
            'c': official['general'],
            'm': official['mode'],
            's': official['categories'],
            'nsfw': official['explicit_content'],
            'e': official['extra'],
            'l': official['language'],
            'g': official['genre'],
            'r': official['rank_achieved'],
            'played': official['played']
        }

        # 组织搜索框参数
        q = ''

        for key, value in params['search'].items():
            if value['eq']:
                if value["min"] is not None:
                    q += f'{key}>={value["min"]} '
                if value["max"] is not None:
                    q += f'{key}<={value["max"]} '
            else:
                if value["min"] is not None:
                    q += f'{key}>{value["min"]} '
                if value["max"] is not None:
                    q += f'{key}<{value["max"]} '
        params_['q'] = q

        first = True
        while True:
            # 达到了数量要求，退出循环，进入下载铺面阶段
            if is_break:
                print(f"[green]达到了数量要求，停止获取铺面")
                print(f"[green]Meet the quantity requirement. Stop getting")
                break

            print(f"开始请求ppy...")
            print(f"Start to get maps...")

            resp = await login_client.search_beatmaps(params=params_)
            # 第一次搜索打印结果
            if first:
                print(f"根据ppy的搜索结果，符合条件的铺面共{resp['total']}张")
                print(f"According to ppy's result, there are {resp['total']} beatmapsets fitting in your condition")
                first = False

            # 获取所有的beatmaps
            beatmapsets = resp['beatmapsets']
            print(f"[green]本次成功获取到了{len(beatmapsets)}张铺面集")
            print(f"[green]Success to get maps, {len(beatmapsets)} total")

            cursor_string: str = resp['cursor_string']
            print(f"新的cursor_string是{cursor_string}")
            print(f"New cursor_string is {cursor_string}")

            params_["cursor_string"] = cursor_string

            # 开始遍历
            exist = 0
            added = 0
            is_break = False
            for beatmapset in beatmapsets:
                # 达到了数量要求，退出
                if len(beatmap_list) >= params['other']['count']:
                    is_break = True
                    break

                if beatmapset['id'] in sid_existed:
                    exist += 1
                    continue

                # 根据官方铺面搜索结果，非已经存在的铺面就是符合条件的铺面
                added += 1
                beatmap_list.append(beatmapset)
            print(f'[green]本次添加了{added}张铺面进入待下载列表')
            print(f'[green]Added {added} beatmapsets to pre-download list')

            if is_break:
                print(f"达到了要求的{params['other']['count']}张铺面")
                print(f"Reached the requirements of quantity {params['other']['count']}")
                break
    return beatmap_list


def on_download_error():
    """
    当下载出错时
    """
    pass


def download_progress_define(total_count):
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


async def download_official(params, scraped_maps):
    """
    使用官方下载源进行下载
    """
    @retry(retry_on_exception=on_download_error)
    async def official_download(download_progress, total_progress, login_client, beatmapset, songs_dir, sem):
        """
        定义了单个铺面下载时的函数
        """
        async with sem:
            n = 0
            async for i in login_client.download_beatmapset(
                    beatmapset['id'],
                    f"{songs_dir}{beatmapset['id']} {illegal_chars.sub('_', beatmapset['artist'])} - {illegal_chars.sub('_', beatmapset['title'])}.osz"
            ):
                if n == 0:
                    download_job = download_progress.add_task(f'[green]{beatmapset["id"]}', total=i)
                if n != 0:
                    download_progress.advance(download_job)
                n += 1
            total_progress.advance(total_task)
            for task in download_progress.tasks:
                if task.finished:
                    task.visible = False

    download_progress, total_progress, progress_table, total_task = download_progress_define(len(scraped_maps))

    # 并发数设置
    sem = asyncio.Semaphore(params['other']['official_sem']['download'])

    # 初始化ppy客户端
    login_client = AsyncLoginClient()
    await login_client.login(params['api']['username'], params['api']['password'])

    # 获取songs的目录
    songs_dir = songsDir()

    # 设置并发任务
    tasks = [
        official_download(
            download_progress=download_progress,
            total_progress=total_progress,
            login_client=login_client,
            beatmapset=beatmapset,
            songs_dir=songs_dir,
            sem=sem
        )
        for beatmapset in scraped_maps
    ]

    # 使用动态进度显示
    with Live(progress_table, refresh_per_second=10, transient=True):
        # 开始任务
        await asyncio.gather(*tasks)


async def main(params):
    print(f'[yellow]正在获取osu!.db，并读取内容...该操作会占用较大内存，视osu!.db的大小而定')
    print(f'[yellow]Getting your osu!.db data...Will take up memory as your osu!.db')

    sid_existed = get_sids_have_existed()

    print(f'[green]获取到了{len(sid_existed)} beatmaps，将不会下载你已经存在的sid的铺面')
    print(f'[green]Got {len(sid_existed)} beatmaps in your osu!.db. Will not download beatmaps in these sids')

    print(f"开始从ppy获取铺面信息，需要获取{params['other']['count']}张铺面。建议开梯子，中国的网络环境你懂的。")
    print(f"Start to get beatmaps from ppy, {params['other']['count']}. "
          f"If you r in China, I suggest you to open your proxy.")

    scraped_maps = await scrape_maps(params, sid_existed)

    print(f"开始下载查询到的铺面")
    print(f"Start download scraped maps")

    if params['other']['mirror'] == 'official':
        await download_official(params, scraped_maps)


if __name__ == "__main__":
    api_params = {
        "api_v2_client_id": 6322,
        "api_v2_client_secret": "G5Dpfd1hAgAt8zkt0aFklV8bteaZITv1vC2bxcf",
        "username": "wanna accuracy",
        "password": ""
    }

    # 搜索参数，用于在ppy官方搜图，详细参数查看packages/osuApiV2.py
    official_params = {
        "general": None,
        "mode": 0,
        "categories": None,
        "explicit_content": True,
        "genre": None,
        "language": None,
        "extra": None,
        "rank_achieved": None,
        "played": None
    }

    # 搜索参数，用于在ppy输入搜索参数
    search_params = {
        "created": {
            "min": 20180101,
            "max": 20210101,
            "eq": True
        },
        "ranked": {
            "min": None,
            "max": None,
            "eq": True
        },
        "star": {
            "min": 6,
            "max": 8,
            "eq": True
        },
        "ar": {
            "min": 9,
            "max": None,
            "eq": True
        },
        "od": {
            "min": None,
            "max": None,
            "eq": True
        },
        "cs": {
            "min": 4,
            "max": 6,
            "eq": True
        },
        "hp": {
            "min": None,
            "max": None,
            "eq": True
        },
        "length": {
            "min": None,
            "max": None,
            "eq": True
        }
    }

    other_params = {
        "count": 200,
        "mirror": "sayobot",
        "sayo_sem": {
            "query": 30,
            "download": 10,
            "use_official": False
        },
        "official_sem": {
            "download": 5
        }
    }

    params = {
        "api": api_params,
        "official": official_params,
        "search": search_params,
        "other": other_params
    }

    # 使用配置文件
    if not os.path.isfile('config.json'):
        print("[red]没有检测到配置文件，已经自动生成，请修改后再次打开")
        print("[red]Cant detect the config.json. "
              "[red]It has been added to your application's root folder. "
              "[red]Please modify the file and try open this later.")
        with open("config.json", "w") as f:
            f.write(json.dumps(params, indent=4))
        exit(0)

    params = json.load(open("config.json", "r"))

    # 运行主程序
    asyncio.get_event_loop().run_until_complete(main(params))
