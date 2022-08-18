import asyncio
import json
import os.path
import re
from typing import List

from retrying import retry
from rich import print
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table

from packages.osuApiV2 import AsyncPpyClient
from packages.osuDirs import songsDir as osu_songs_dir_get, osuDirGet
from packages.osu_db.osu_db import read_osu_db
from packages.sayobotApi import AsyncSayobot


def on_error():
    pass


def compare_interval(l: list, num: int, equal: bool = True):
    """
    比较一个数字是否在一个区间内
    :param l:
    :param num:
    :param equal: 是否包含相等
    :return:
    """
    r = False
    if equal:
        if num >= l[0]:
            if num <= l[1]:
                r = True
    else:
        if num > l[0]:
            if num < l[1]:
                r = True
    return r


async def main(
        api_v2_client_id: int,
        api_v2_client_secret: str,
        username: str,
        password: str,
        total_length_asked: List[int | int],
        ar_asked: List[int | int],
        od_asked: List[int | int],
        cs_asked: List[int | int],
        hp_asked: List[int | int],
        star_asked: List[int | int],
        bpm_asked: List[int | int],
        count_asked: int,
        sayo_mirror: bool,
        params: dict,
        sayo_sem: int,
        download_sem: int
):
    ppy_client = AsyncPpyClient()

    print(f"正在初始化osu api client，获取api所需的token...")
    await ppy_client.initialization(client_id=api_v2_client_id,
                                    client_secret=api_v2_client_secret)
    print(f"[green]获取成功")
    print(f'正在尝试登录ppy...')
    await ppy_client.init_login(username, password)
    print(f'[green]登录成功')

    beatmap_list = []
    is_break = False

    print(f'[yellow]正在获取osu!.db，并读取内容...该操作会占用较大内存，视osu!.db的大小而定')
    osu_db_info = read_osu_db(osuDirGet() + 'osu!.db')
    sids_have_existed = list(set([beatmap['beatmap_set_id'] for beatmap in osu_db_info['beatmaps']]))

    # ###################################### 搜刮铺面 ######################################## #
    print(f"开始获取指定数量{count_asked}的铺面")
    # 开始进入铺面搜索的循环
    while True:
        # 达到了数量要求，退出循环，进入下载铺面阶段
        if is_break:
            print(f"[green]达到了数量要求，停止获取铺面")
            break

        print(f"开始请求ppy...")
        resp = await ppy_client.search_beatmaps(params=params)
        cursor_string: str = resp['cursor_string']
        beatmapsets = resp['beatmapsets']
        print(f"[green]本次成功获取到了{len(beatmapsets)}张铺面集")
        print(f"[green]新的cursor_string是{cursor_string}")

        # 为新一轮的搜索添加cursor_string
        params['cursor_string'] = cursor_string

        # 循环搜索到的一堆铺面集，一般是五十个
        for beatmapset in beatmapsets:
            # 使用一个变量存储状态，如果为True，把铺面的sid加入到beatmap_list中
            is_pass = False
            # 循环铺面集内的各个铺面，进行筛选
            for beatmap in beatmapset['beatmaps']:
                beatmap: dict

                # 下方几个参数都是布尔值，不写注解了，累得慌
                total_length = compare_interval(total_length_asked, beatmap['total_length'])
                ar = compare_interval(ar_asked, beatmap['ar'])
                od = compare_interval(od_asked, beatmap['accuracy'])
                cs = compare_interval(cs_asked, beatmap['cs'])
                hp = compare_interval(hp_asked, beatmap['drain'])
                bpm = compare_interval(bpm_asked, beatmap['bpm'])
                star = compare_interval(star_asked, beatmap['difficulty_rating'])

                is_existed = (beatmapset['id'] in sids_have_existed)

                condition1 = False in [total_length, ar, od, cs, hp, bpm, star]
                condition2 = is_existed

                condition = (not condition1) and (not condition2)

                if condition:
                    is_pass = True
                    break

            if is_pass:
                print(f"[green]sid:{beatmapset['id']}符合条件，加入到待下载列表")
                beatmap_list.append(beatmapset['id'])
            else:
                print(f"sid:{beatmapset['id']}不符合条件，跳过")

            # 筛掉重复铺面
            beatmap_list = list(set(beatmap_list))

            if len(beatmap_list) >= count_asked:
                is_break = True
                break

    # ###################################### 下载源的判断 ######################################## #

    # 是否使用sayo镜像站进行下载，如果是，就去sayo查询铺面信息，如果能查到就将下载源改为sayo，否则下载源为official
    # 如果在sayo查到了信息，顺便将所需信息放入beatmapsets_info
    if sayo_mirror:
        print('sayo的下载开关已经打开，将尽量使用小夜进行下载')
        print('开始向小夜请求铺面数据，请求到的使用小夜下载，没请求到的使用官方下载')
        sayo_client = AsyncSayobot(
            referer=r'https://gitrepo.frzzmeow.icu/frz/pyOsuTools',
            user_agent='pyOsuTools'
        )
        beatmapsets_list_query = []

        @retry(retry_on_exception=on_error)
        async def sayo_check(sid: int, sem: asyncio.Semaphore):
            """
            检查sid是否存在于sayobot
            :param sem: 最大并发数
            :param sid:
            :return:
            """
            async with sem:
                sayo_resp = await sayo_client.beatmap_info_v2(k=sid)

                is_no_params = (sayo_resp == {"status": 114514})
                is_no_map = (sayo_resp == {"status": -1})

                if is_no_map or is_no_params:
                    beatmapsets_list_query.append({'sid': sid, "from": "official"})
                    if is_no_map:
                        print(f"将{sid}分入official进行下载，因为小夜没有")
                    if is_no_params:
                        print(f"[red]将{sid}分入official进行下载，因为根本没写参数，怎么去小夜查")
                else:
                    beatmapsets_list_query.append({'sid': sid, "from": "sayo"})
                    print(f"将{sid}分入sayo进行下载")

        print(f"限制查询的最大并发数为{sayo_sem}")
        sem = asyncio.Semaphore(sayo_sem)
        tasks = [sayo_check(sid=sid, sem=sem) for sid in beatmap_list]
        await asyncio.gather(*tasks)
    else:
        print(f"没有打开小夜下载，将全部使用官方进行下载")
        beatmapsets_list_query = [{'sid': sid, "from": "official"} for sid in beatmap_list]

    # ###################################### 获取铺面信息 ######################################## #
    print('开始获取铺面信息')
    # 该dict以sid为键
    beatmapsets_info = {}

    beatmapsets_query_sayo = []
    beatmapsets_query_official = []
    for beatmap in beatmapsets_list_query:
        if beatmap['from'] == 'sayo':
            beatmapsets_query_sayo.append(beatmap['sid'])
        elif beatmap['from'] == 'sayo':
            beatmapsets_query_official.append(beatmap['sid'])

    # sayo查信息
    if sayo_mirror:
        print(f'向sayo获取{len(beatmapsets_query_sayo)}张铺面信息，并发数为{sayo_sem}')
        if len(beatmapsets_query_sayo) != 0:
            @retry(retry_on_exception=on_error)
            async def sayo_query(sid: int, sem: asyncio.Semaphore):
                """
                向sayo请求铺面信息并添加到
                :param sid:
                :param sem: 并发数
                :return:
                """
                async with sem:
                    sayo_resp: dict = (await sayo_client.beatmap_info_v2(k=sid))['data']
                    beatmapsets_info[sayo_resp['sid']] = {
                        'sid': sayo_resp['sid'],
                        'title': sayo_resp['title'],
                        'artist': sayo_resp['artist'],
                        'from': 'sayo'
                    }
                    print(f'{sayo_resp["sid"]}获取完毕')

            sem = asyncio.Semaphore(sayo_sem)
            tasks = [sayo_query(sid, sem) for sid in beatmapsets_query_sayo]
            await asyncio.gather(*tasks)

    if len(beatmapsets_query_official) != 0:
        print(f'[orange]开始向ppy获取{len(beatmapsets_query_official)}张铺面信息，由于请求限制，获取较慢')
        for sid in beatmapsets_query_official:
            @retry(retry_on_exception=on_error)
            async def get_beatmapsets(sid: int):
                return await ppy_client.get_beatmapsets(sid)

            resp = await get_beatmapsets(sid)
            beatmapsets_info[resp['id']] = {
                'sid': resp['id'],
                'title': resp['title'],
                'artist': resp['artist'],
                'from': 'official'
            }
            await asyncio.sleep(1)
            print(f'{resp["id"]}获取完毕')

    # ###################################### 下载进度条的初始化 ######################################## #
    # 创建进度显示的类
    # 分下载的进度类
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

    total_task = total_progress.add_task('[yellow]Total', total=len(beatmapsets_info))

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

    illegal_chars = re.compile(r"[\<\>:\"\/\\\|\?*]")
    tasks = []
    songs_dir = osu_songs_dir_get()

    # 进入小夜下载
    if sayo_mirror:
        if any(info['from'] == 'sayo' for key, info in beatmapsets_info.items()):
            @retry(retry_on_exception=on_error)
            async def sayo_download(sid: int, fp: str, sem: asyncio.Semaphore):
                async with sem:
                    n = 0
                    async for i in sayo_client.download_beatmapset(sid, fp):
                        if n == 0:
                            download_job = download_progress.add_task(f'[green]{sid}', total=i)
                        if n != 0:
                            download_progress.advance(download_job)
                        n += 1
                    total_progress.advance(total_task)
                    # 检测是否完成，完成的隐藏
                    for task in download_progress.tasks:
                        if task.finished:
                            task.visible = False

            sem = asyncio.Semaphore(download_sem)

            tasks = [sayo_download(
                sid=info['sid'],
                fp=f"{songs_dir}{info['sid']} {illegal_chars.sub('_', info['artist'])} - {illegal_chars.sub('_', info['title'])}.osz",
                sem=sem
            ) for key, info in beatmapsets_info.items() if info['from'] == 'sayo']

            with Live(progress_table, refresh_per_second=10):
                await asyncio.gather(*tasks)

    # 进入官方下载
    if any(info['from'] == 'official' for key, info in beatmapsets_info.items()):
        with Live(progress_table, refresh_per_second=10, transient=True):
            for key, info in beatmapsets_info.items():
                if info['from'] == 'official':

                    @retry(retry_on_exception=on_error)
                    async def official_download():
                        n = 0
                        async for i in ppy_client.download_beatmapset(
                                info['sid'],
                                f"{songs_dir}{info['sid']} {illegal_chars.sub('_', info['artist'])} - {illegal_chars.sub('_', info['title'])}.osz"
                        ):
                            if n == 0:
                                download_job = download_progress.add_task(f'[green]{info["sid"]}', total=i)
                            if n != 0:
                                download_progress.advance(download_job)
                        total_progress.advance(total_task)
                        for task in download_progress.tasks:
                            if task.finished:
                                task.visible = False

                    await official_download()

    print('[green]下载完毕，回车退出')
    input()


if __name__ == '__main__':
    # ###### 编辑输入参数区 ###### #
    api_v2_client_id = 6322
    api_v2_client_secret = "G5Dpfd1hAgAt8zkt0aFklV8bteaZITv1vC2bxcfO"
    username = 'wanna accuracy'
    password = 'qwsa1234'
    # 搜索参数，用于在ppy官方搜图，详细参数查看packages/osuApiV2.py line:72
    params = {
        'm': 0,
        'nsfw': True
    }

    # 长度按秒算
    total_length_asked = [120, 360]
    ar_asked = [9.2, 10]
    od_asked = [0, 10]
    cs_asked = [4, 5.2]
    hp_asked = [0, 10]
    star_asked = [6, 8]
    bpm_asked = [150, 280]
    # 下载数量
    count_asked = 30

    # 是否使用小夜下载源，如果小夜没图，就从官方下
    sayo_mirror = True

    # 向sayobot查询铺面时的最大并发数
    sayo_sem = 10

    # 下载时的最大并发数
    download_sem = 10
    # ###### 编辑输入参数区 ###### #

    # ###### 如果被编译了就用config.ini里的参数 ###### #
    # 是否打算被编译(是否使用config.ini里的参数)
    is_config_ini = True

    if is_config_ini:
        if not os.path.isfile('config.json'):
            print('[red]未检测到配置文件，已经创建config.json，请修改config.json内的内容后再次打开。')
            print('[red]详情参数请参考：'
                  'https://gitrepo.frzzmeow.icu/frz/pyOsuTools/src/branch/master/%E4%B8%8B%E8%BD%BD%E9%93%BA%E9%9D%A2')
            with open('config.json', 'w') as f:
                config = {
                    'params': {
                        'c': None,
                        'm': None,
                        's': None,
                        'nsfw': None,
                        'e': None,
                        'r': None,
                        'played': None,
                        'l': None,
                        'g': None
                    },
                    'api': {
                        'v2': {
                            'id': 114514,
                            'secret': "Your secret"
                        },
                        'login': {
                            'username': 'You osu username',
                            'password': 'Password here'
                        }
                    },
                    'total_length': {
                        'min': 1,
                        'max': 300
                    },
                    'ar': {
                        'min': 0,
                        'max': 10
                    },
                    'cs': {
                        'min': 0,
                        'max': 10
                    },
                    'od': {
                        'min': 0,
                        'max': 10
                    },
                    'hp': {
                        'min': 0,
                        'max': 10
                    },
                    'bpm': {
                        'min': 0,
                        'max': 1000
                    },
                    'star': {
                        'min': 0,
                        'max': 10
                    },
                    'count': 200,
                    'sayo_mirror': True,
                    'sayo_sem': 10,
                    'download_sem': 10
                }
                json.dump(config, f, indent=4)
            input()
            exit(0)
        config = json.load(open('config.json', 'r'))

        api_v2_client_id = config['api']['v2']['id']
        api_v2_client_secret = config['api']['v2']['secret']
        username = config['api']['login']['username']
        password = config['api']['login']['password']
        params = config['params']
        total_length_asked = [config['total_length']['min'], config['total_length']['max']]
        ar_asked = [config['ar']['min'], config['ar']['max']]
        od_asked = [config['od']['min'], config['od']['max']]
        cs_asked = [config['cs']['min'], config['cs']['max']]
        hp_asked = [config['hp']['min'], config['hp']['max']]
        star_asked = [config['star']['min'], config['star']['max']]
        bpm_asked = [config['bpm']['min'], config['bpm']['max']]
        count_asked = config['count']
        sayo_mirror = config['sayo_mirror']
        sayo_sem = config['sayo_sem']
        download_sem = config['download_sem']

    # ############################################################################## #
    # 以下为主程序
    asyncio.get_event_loop().run_until_complete(main(
        api_v2_client_id=api_v2_client_id,
        api_v2_client_secret=api_v2_client_secret,
        username=username,
        password=password,
        params=params,
        total_length_asked=total_length_asked,
        ar_asked=ar_asked,
        od_asked=od_asked,
        cs_asked=cs_asked,
        hp_asked=hp_asked,
        star_asked=star_asked,
        bpm_asked=bpm_asked,
        count_asked=count_asked,
        sayo_mirror=sayo_mirror,
        sayo_sem=sayo_sem,
        download_sem=download_sem
    ))
