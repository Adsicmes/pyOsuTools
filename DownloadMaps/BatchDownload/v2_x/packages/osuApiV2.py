import asyncio
import re

import httpx
import json
import aiofiles
from httpx import Response
from lxml import etree
from typing import *


class AsyncPpyClient:
    """
    api具有每分钟60次的访问限制
    非api不稳定，可能炸
    """
    def __init__(self):
        """
        initial the session
        """
        self.api_client: httpx.AsyncClient = httpx.AsyncClient(timeout=36000, verify=False)
        self.login_client: httpx.AsyncClient = httpx.AsyncClient(timeout=36000, verify=False)

    async def init_login(self, username: str, password: str):
        homepage = await self.login_client.get(r'https://osu.ppy.sh/home')
        regex = re.compile(r".*?csrf-token.*?content=\"(.*?)\">", re.DOTALL)
        match = regex.match(homepage.text)
        csrf_token = match.group(1)
        data = {
            'username': username,
            'password': password,
            "_token": csrf_token
        }
        headers = {"referer": r'https://osu.ppy.sh/home'}
        await self.login_client.post(r"https://osu.ppy.sh/session", data=data, headers=headers)

    async def initialization(self, client_id: int, client_secret: str) -> httpx.AsyncClient:
        """
        initial the token according to the given params

        :param client_id: your osu api v2 client id
        :param client_secret: your osu api v2 client secret
        :return: a httpx Client instant
        """
        token_url: str = "https://osu.ppy.sh/oauth/token"
        post_data: dict = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "public"
        }
        resp: Response = await self.api_client.post(url=token_url, data=post_data)
        resp: dict = resp.json()

        self.api_client.headers["Authorization"]: str = f"Bearer {resp['access_token']}"

        return self.api_client

    async def get_beatmap(self, beatmap: int) -> dict:
        """
        Gets beatmap data for the specified beatmap ID.

        :param beatmap: beatmap id
        :return: beatmap object
        """
        url = f"https://osu.ppy.sh/api/v2/beatmaps/{beatmap}"
        resp: Response = await self.api_client.get(url)
        return resp.json()

    async def get_beatmaps(self, ids: List[int]) -> dict:
        """
        Returns list of beatmaps.

        :param ids: Beatmap id to be returned. Specify once for each beatmap id requested.
                    Up to 50 beatmaps can be requested at once.
        :return: beatmaps list
        """
        if not ids:
            return {
                "beatmaps": [
                ]
            }

        url = f"https://osu.ppy.sh/api/v2/beatmaps"
        id_str = ''
        for i in ids:
            id_str += f"{i},"
        id_str = id_str[:-1]
        resp: Response = await self.api_client.get(url, params={'ids[]': id_str})
        return resp.json()

    async def get_beatmapsets(self, sid: int) -> dict:
        """
        非api
        获取beatmapsets，返回详见Examples/osuApiV2/beatmapset.json
        :param sid:
        :return:
        """
        url = f'https://osu.ppy.sh/beatmapsets/{sid}'
        resp = await self.login_client.get(url)
        con = etree.HTML(resp.content, parser=etree.HTMLParser(encoding='utf-8'))
        result: str = con.xpath('//script[@id="json-beatmapset"]/text()')[0]
        return json.loads(result.strip())

    async def get_beatmapset_comments(self,
                                      sid: int,
                                      sort: str = 'new',
                                      parent_id: Optional[int] = None,
                                      cursor_votes_count: Optional[int] = None,
                                      cursor_id: Optional[int] = None,
                                      cursor_created_at: Optional[str] = None):
        """
        获取铺面集的评论

        如果返回的结果中has_more的结果为True，那么可以通过本次结果中的cursor(三个)获取下一批评论
        :param sid:
        :param sort: top(热门) new old
        :param parent_id: Limit to comments which are reply to the specified id. Specify 0 to get top level comments.
        :param cursor_votes_count:
        :param cursor_id:
        :param cursor_created_at:
        :return:
        """
        params = {
            'commentable_type': 'beatmapset',
            'commentable_id': sid,
            'sort': sort,
            'parent_id': parent_id,
            'cursor[id]': cursor_id,
            'cursor[create_at]': cursor_created_at,
            'cursor[votes_count]': cursor_votes_count
        }
        url = r'https://osu.ppy.sh/comments'
        resp = await self.api_client.get(url, params=params)
        return resp.json()

    async def search_beatmaps(
            self,
            params: dict = None,
            c: str = None,
            m: int = None,
            s: str = None,
            nsfw: bool = True,
            e: str = None,
            r: str = None,
            played: str = None,
            l: int = None,
            g: int = None,
            cursor_string: str = None
    ) -> dict:
        """
        played和r只能撒泼特使用
        以下参数组合使用'.'连接
        是否可以组合用 Y/N 表示
        :param params: 方便自由组合参数
        :param c: Y recommended(推荐难度) converts(包括转铺) follows(已关注铺师) spotlights(聚光灯) featured_artists(精选艺术家)
        :param m: N 0=std 1=taiko 2=catch 3=mania
        :param s: N any 不填(计入排名) ranked qualified loved favourites(收藏夹) pending wip(制作中) graveyard mine(我的)
        :param nsfw: N
        :param e: Y video storyboard
        :param r: Y XH X SH S A B C D
        :param played: N played unplayed
        :param l: N 1=未指定 2=English 3=Japanese 4=Chinese 5=Instrumental 6=Korean 7=French 8=Germany
         9=Swedish 10=Spanish 11=Italian 12=Russian 13=Polish 14=others
        :param g: N 1=未指定 2=电子游戏 3=动漫 4=摇滚 5=流行乐 6=其他 7=新奇 9=嘻哈 10=电子 11=金属 12=古典 13=民谣 14=爵士
        :param cursor_string: 用于接续之前的搜索
        :return:
        """
        if params is None:
            params = {
                'c': c,
                'm': m,
                's': s,
                'nsfw': nsfw,
                'e': e,
                'r': r,
                'played': played,
                'l': l,
                'g': g,
                'cursor_string': cursor_string
            }
        else:
            params = params

        url = r'https://osu.ppy.sh/beatmapsets/search'
        resp = await self.login_client.get(url, params=params)
        return resp.json()

    async def get_mp(self, mp_id: int) -> dict:
        """
        非api
        获取到mp房间的信息
        :param mp_id: id 一定是id 不能是房间名
        :return:
        """
        url = f'https://osu.ppy.sh/community/matches/{mp_id}'
        resp = await self.api_client.get(url)
        # print(resp.content)
        con = etree.HTML(resp.content, parser=etree.HTMLParser(encoding='utf-8'))
        result: str = con.xpath('//script[@id="json-events"]/text()')[0]
        return json.loads(result.strip())

    async def download_beatmapset(self, sid: int, fp: str, nv: bool = False):
        """
        从官网下载指定的铺面
        这是一个生成器，可以使用for循环进行循环
        使用了yield返回True
        返回的内容如下:
            第一次返回的是会写入的次数(headers里的content-length/1024为总kb数，总kb数/16即为写入次数，一次写入16kb)
            之后的yield返回的True全部代表为成功下载写入了一个区块
        :param fp: 下载到的 文件路径
        :param sid:
        :param nv: 是否下载无视频  True下载无视频
        :return:
        """
        url = f'https://osu.ppy.sh/beatmapsets/{sid}/download'
        url = url + '?noVideo=1' if nv else url
        headers = {'referer': f'https://osu.ppy.sh/beatmapsets/{sid}/'}

        # 获取回调网址    
        resp = await self.login_client.get(url, follow_redirects=False, headers=headers)
        redirect_download_url = resp.headers['location']

        # 进入流下载
        async with self.login_client.stream('GET', redirect_download_url) as stream:
            # 获取写入次数
            chunk_count = int(stream.headers['content-length'])/1024/16
            # 返回写入次数
            yield int(chunk_count) + 1 if chunk_count > int(chunk_count) else chunk_count
            # 异步写入文件
            async with aiofiles.open(fp, 'wb') as f:
                # 对所有的原始内容进行迭代
                async for chunk in stream.aiter_raw():
                    await f.write(chunk)
                    # 返回信号，表示成功写入一次
                    yield True


class PpyClient:
    def __init__(self):
        pass


async def main():
    client = AsyncPpyClient()
    await client.initialization(6322, "G5Dpfd1hAgAt8zkt0aFklV8bteaZITv1vC2bxcfO")

    await client.init_login('wanna accuracy', 'qwsa1234')

    n = 0
    async for i in client.download_beatmapset(705224, "download.osz", nv=True):
        if n == 0:
            total: int = i
            print(f'总区块数量为{total}')
        print(n, end='\r')
        n += 1

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
