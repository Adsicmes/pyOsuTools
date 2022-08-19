import asyncio
import re

import httpx
import json
import aiofiles
from httpx import Response
from lxml import etree
from typing import *


class AsyncLoginClient:
    """
    非api不稳定，可能炸
    """

    def __init__(self, timeout: int = 36000):
        """
        initial the session
        """
        self.login_client: httpx.AsyncClient = httpx.AsyncClient(timeout=timeout, verify=False)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.logout()
        return

    async def login(self, username: str, password: str):
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

    async def logout(self):
        """
        用于退出登录ppy
        """
        homepage = await self.login_client.get(r'https://osu.ppy.sh/home')
        regex = re.compile(r".*?csrf-token.*?content=\"(.*?)\">", re.DOTALL)
        match = regex.match(homepage.text)
        csrf_token = match.group(1)

        headers = {
            "referer": r'https://osu.ppy.sh/home',
            "x-csrf-token": csrf_token
        }
        cookies = {
            "XSRF-TOKEN": csrf_token,
        }
        await self.login_client.delete("https://osu.ppy.sh/session", headers=headers, cookies=cookies)

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
            chunk_count = int(stream.headers['content-length']) / 1024 / 16
            # 返回写入次数
            yield int(chunk_count) + 1 if chunk_count > int(chunk_count) else chunk_count
            # 异步写入文件
            async with aiofiles.open(fp, 'wb') as f:
                # 对所有的原始内容进行迭代
                async for chunk in stream.aiter_raw():
                    await f.write(chunk)
                    # 返回信号，表示成功写入一次
                    yield True

    async def search_beatmaps(
            self,
            params: dict = None,
            q: str = None,
            c: str = None,
            m: int = None,
            s: str = None,
            nsfw: bool = True,
            e: str = None,
            r: str = None,
            played: str = None,
            l: int = None,
            g: int = None,
            cursor_string: str = None,
            sort: str = None
    ) -> dict:
        """
        played和r只能撒泼特使用
        以下参数需要组合使用'.'连接
        是否可以组合用 Y/N 表示

        :param params:
            自定义参数列表，若本参数不为空，则其他参数无效
        :param q:
            osu搜索框
        :param c: Y
            recommended(推荐难度) converts(包括转铺) follows(已关注铺师) spotlights(聚光灯) featured_artists(精选艺术家)
        :param m: N
            0=std 1=taiko 2=catch 3=mania
        :param s: N
            any 不填(计入排名) ranked qualified loved favourites(收藏夹) pending wip(制作中) graveyard mine(我的)
        :param nsfw: N
            bool值
        :param e: Y
            video storyboard
        :param r: Y
            XH X SH S A B C D
        :param played: N
            played unplayed
        :param l: N
            1=未指定 2=English 3=Japanese 4=Chinese 5=Instrumental 6=Korean 7=French 8=Germany
            9=Swedish 10=Spanish 11=Italian 12=Russian 13=Polish 14=others
        :param g: N
            1=未指定 2=电子游戏 3=动漫 4=摇滚 5=流行乐 6=其他 7=新奇 9=嘻哈 10=电子 11=金属 12=古典 13=民谣 14=爵士
        :param cursor_string:
            用于接续之前的搜索
        :param sort:
            返回结果的排序
        :return:
        """
        if params is None:
            params = {
                'q': q,
                'c': c,
                'm': m,
                's': s,
                'nsfw': nsfw,
                'e': e,
                'r': r,
                'played': played,
                'l': l,
                'g': g,
                'cursor_string': cursor_string,
                'sort': sort
            }
        else:
            params = params

        # 清除为空的参数
        del_list = []
        for key, value in params.items():
            if value is None:
                del_list.append(key)
        for key in del_list:
            del params[key]

        url = r'https://osu.ppy.sh/beatmapsets/search'
        resp = await self.login_client.get(url, params=params)
        return resp.json()


class AsyncApiClient:
    """
    api具有每分钟60次的访问限制
    """

    def __init__(self, timeout: int = 36000):
        """
        initial the session
        """
        self.api_client: httpx.AsyncClient = httpx.AsyncClient(timeout=timeout, verify=False)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return

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

    async def get_user(self, user: Union[int | str], key: str = "username", mode: str = "osu") -> dict:
        """
        获取单个用户的信息
        :param key: 查询的用户的类型 可填"id"或"username" 默认"username"
        :param user: 用户名或者id
        :param mode: 模式的字符串 详见 https://osu.ppy.sh/docs/index.html#gamemode
        :return:
        """
        params = {"key": key}

        url = f"https://osu.ppy.sh/api/v2/users/{user}/{mode}"
        resp = await self.api_client.get(url, params=params)
        return resp.json()

    async def get_user_scores(
            self,
            user: int,
            score_type: str,
            include_fails: int = 0,
            mode: str = "osu",
            limit: int = 50,
            offset: int = 0
    ) -> list | dict:
        """
        获取用户的分数 可以获取bp，recent, firsts(第一名)
        :param user: 用户id
        :param score_type: 分数类型 可选best, firsts, recent
        :param include_fails: 是否包含fail的成绩 0是不包含 1是包含
        :param mode: 游戏模式 默认"osu" 详见 https://osu.ppy.sh/docs/index.html#gamemode
        :param limit: 一次请求限制 最大50
        :param offset: 查询偏移
        :return:
        """
        params = {
            "include_fails": include_fails,
            "mode": mode,
            "limit": limit,
            "offset": offset
        }
        url = f"https://osu.ppy.sh/api/v2/users/{user}/scores/{score_type}"

        resp = await self.api_client.get(url, params=params)
        return resp.json()

    async def get_user_best(self, user: Union[str | int], mode: str = "osu") -> list:
        """
        获取用户所有的bp，100个
        :param user: id或者name
        :param mode: 游戏模式 默认”osu“
        :return:
        """
        if type(user) == str:
            user_id = (await self.get_user(user))['id']
        else:
            user_id = user

        part1 = await self.get_user_scores(user_id, score_type='best', mode=mode)
        part2 = await self.get_user_scores(user_id, score_type='best', mode=mode, offset=50)

        all_scores = part1 + part2
        return all_scores

    async def get_map_attributes(self, beatmap: int, mods: list[str] = None, ruleset: str = None):
        """
        获取铺面带mod或转换模式后的具体信息
        :param beatmap: 铺面id
        :param mods: 铺面mod列表，如["HR", "HD"]
        :param ruleset: 游戏模式，默认为铺面默认模式，为字符串
        :return:
        """
        url = f"https://osu.ppy.sh/api/v2/beatmaps/{beatmap}/attributes"

        data = {}

        if mods:
            # mod_to_post = []
            # if 'HR' in mod_to_post:
            #     mod_to_post += 'HR'
            # if 'DT' in mod_to_post or "NC" in mod_to_post:
            #     mod_to_post += 'DT'
            # if 'FL' in mod_to_post:
            #     mod_to_post += 'FL'
            # if 'EZ' in mod_to_post:
            #     mod_to_post += 'EZ'
            # if 'HT' in mod_to_post:
            #     mod_to_post += 'HT'

            data["mods[]"] = mods

        if ruleset:
            data['ruleset'] = ruleset

        resp = await self.api_client.post(url, data=data)

        return resp.json()


async def main():
    client = AsyncLoginClient()
    await client.login("wanna accuracy", "qwsa1234")
    await client.get_beatmapsets(1825999)
    await client.logout()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
