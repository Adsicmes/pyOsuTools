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


class DownloadParams:
    api_v2_client_id: int
    api_v2_client_secret: str
    username: str
    password: str
    total_length_asked: List[int | int]
    ar_asked: List[int | int]
    od_asked: List[int | int]
    cs_asked: List[int | int]
    hp_asked: List[int | int]
    star_asked: List[int | int]
    bpm_asked: List[int | int]
    count_asked: int
    sayo_mirror: bool
    params: dict
    sayo_sem: int
    download_sem: int

    def __init__(
            self,
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
        self.api_v2_client_secret = api_v2_client_secret
        self.api_v2_client_id = api_v2_client_id
        self.username = username
        self.password = password
        self.total_length_asked = total_length_asked
        self.ar_asked = ar_asked
        self.od_asked = od_asked
        self.cs_asked = cs_asked
        self.hp_asked = hp_asked
        self.star_asked = star_asked
        self.bpm_asked = bpm_asked
        self.count_asked = count_asked
        self.sayo_mirror = sayo_mirror
        self.params = params
        self.sayo_sem = sayo_sem
        self.download_sem = download_sem


class Downloader:
    def __init__(
            self,
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
        self.download_params = DownloadParams(
            api_v2_client_id,
            api_v2_client_secret,
            username,
            password,
            total_length_asked,
            ar_asked,
            od_asked,
            cs_asked,
            hp_asked,
            star_asked,
            bpm_asked,
            count_asked,
            sayo_mirror,
            params,
            sayo_sem,
            download_sem
        )

    def scrape_maps(self):
        params = self.download_params.params
        count = self.download_params.count_asked



