import asyncio
from typing import *

import aiofiles
import httpx


class AsyncSayobot:

    def __init__(self, referer: str = None, user_agent: str = None):
        headers = {
            "referer": referer,
            "user_agent": user_agent
        }

        key_del = []
        for key, value in headers.items():
            if value is None:
                key_del.append(key)
        for key in key_del:
            del headers[key]

        self.client = httpx.AsyncClient(headers=headers, verify=False, timeout=36000)

    async def beatmap_info_v1(self,
                              b: Optional[int] = None,
                              s: Optional[int] = None,
                              k: Optional[str] = None) -> dict:
        """
        sayo查询beatmap的v1 api
        如果没查到返回{"status":-1}
        如果没参数返回{"status": 1145141919810}

        :param b: bid 优先级低
        :param s: sid 优先级最高
        :param k: keyword 可以是官网Url链接、sid、bid，优先级最低
        :return:
        """
        url = r'https://api.sayobot.cn/beatmapinfo'

        params = {
            's': s,
            'b': b,
            'k': k
        }

        # 检测参数列表是否非空，是空的就返回114514
        if not params:
            return {"status": 114514}

        resp = await self.client.get(url, params=params)
        return resp.json()

    async def beatmap_info_v2(self,
                              k: int,
                              t: Optional[int] = 0) -> dict:
        """
        sayo查询beatmap的v2 api
        如果没查到返回{"status":-1}
        如果没参数返回{"status": 1145141919810}

        :param k: keyword 关键字
        :param t: type 0为自动匹配 1为bid
        :return:
        """
        url = r'https://api.sayobot.cn/v2/beatmapinfo'

        params = {
            'k': k,
            't': t
        }

        # 检测参数列表是否非空，是空的就返回114514
        if not params:
            return {"status": 114514}

        resp = await self.client.get(url, params=params)
        return resp.json()

    async def download_beatmapset(self, sid: int, fp: str, nv: bool = False, mini: bool = False):
        """
        从小夜下载指定的铺面
        这是一个生成器，可以使用for循环进行循环
        使用了yield返回True
        返回的内容如下:
            第一次返回的是会写入的次数(headers里的content-length/1024为总kb数，总kb数/16即为写入次数，一次写入16kb)
            之后的yield返回的True全部代表为成功下载写入了一个区块
        :param sid:
        :param fp:
        :param nv: 优先级比mini高，如果两个都为True，那么下载类型为noVideo
        :param mini:
        :return:
        """
        dl_type = False

        if nv:
            dl_type = 'novideo'

        if (not dl_type) and mini:
            dl_type = 'mini'

        if not dl_type:
            dl_type = 'full'

        url = f"https://dl.sayobot.cn/beatmaps/download/{dl_type}/{sid}"
        resp = await self.client.get(url, follow_redirects=False)
        url = resp.headers['location']

        async with self.client.stream("GET", url) as stream:
            chunk_count = int(stream.headers['content-length']) / 1024 / 16
            yield int(chunk_count) + 1 if chunk_count > int(chunk_count) else chunk_count
            async with aiofiles.open(fp, 'wb') as f:
                async for chunk in stream.aiter_raw():
                    await f.write(chunk)
                    yield True


class Sayobot:

    def __init__(self, referer: str = None, user_agent: str = None):
        headers = {
            "referer": referer,
            "user_agent": user_agent
        }

        # ...

        self.client = httpx.Client(headers=headers, verify=False, timeout=36000)

    def beatmap_info_v1(self,
                        b: Optional[int] = None,
                        s: Optional[int] = None,
                        k: Optional[str] = None) -> dict:
        """
        sayo查询beatmap的v1 api
        如果没查到返回{"status":-1}
        如果没参数返回{"status": 1145141919810}

        :param b: bid 优先级低
        :param s: sid 优先级最高
        :param k: keyword 可以是官网Url链接、sid、bid，优先级最低
        :return:
        """
        url = r'https://api.sayobot.cn/beatmapinfo'

        params = {
            's': s,
            'b': b,
            'k': k
        }

        # 检测参数列表是否非空，是空的就返回114514
        if not params:
            return {"status": 114514}

        resp = self.client.get(url, params=params)
        return resp.json()

    def beatmap_info_v2(self,
                        k: int,
                        t: Optional[int] = 0) -> dict:
        """
        sayo查询beatmap的v2 api
        如果没查到返回{"status":-1}
        如果没参数返回{"status": 1145141919810}

        :param k: keyword 关键字
        :param t: type 0为自动匹配 1为bid
        :return:
        """
        url = r'https://api.sayobot.cn/v2/beatmapinfo'

        params = {
            'k': k,
            't': t
        }

        # 检测参数列表是否非空，是空的就返回114514
        if not params:
            return {"status": 114514}

        resp = self.client.get(url, params=params)
        return resp.json()

    def download_beatmapset(self, sid: int, fp: str, nv: bool = False, mini: bool = False):
        """
        从小夜下载指定的铺面
        这是一个生成器，可以使用for循环进行循环
        使用了yield返回True
        返回的内容如下:
            第一次返回的是会写入的次数(headers里的content-length/1024为总kb数，总kb数/16即为写入次数，一次写入16kb)
            之后的yield返回的True全部代表为成功下载写入了一个区块
        :param sid:
        :param fp:
        :param nv: 优先级比mini高，如果两个都为True，那么下载类型为noVideo
        :param mini:
        :return:
        """
        dl_type = False

        if nv:
            dl_type = 'novideo'

        if (not dl_type) and mini:
            dl_type = 'mini'

        if not dl_type:
            dl_type = 'full'

        url = f"https://dl.sayobot.cn/beatmaps/download/{dl_type}/{sid}"
        resp = self.client.get(url, follow_redirects=False)
        url = resp.headers['location']

        with self.client.stream("GET", url) as stream:
            chunk_count = int(stream.headers['content-length']) / 1024 / 16
            yield int(chunk_count) + 1 if chunk_count > int(chunk_count) else chunk_count
            with aiofiles.open(fp, 'wb') as f:
                for chunk in stream.aiter_raw():
                    f.write(chunk)
                    yield True


async def main():
    client = AsyncSayobot(referer="", user_agent='')
    n = 0
    async for i in client.download_beatmapset(705224, "download.osz", nv=True):
        if n == 0:
            total: int = i
            print(f'总区块数量为{total}')
        print(n, end='\r')
        n += 1


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
