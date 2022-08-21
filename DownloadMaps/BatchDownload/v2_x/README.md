# 介绍(Introduce)

文档追随最新版本，旧版本不予支持

Document follows the latest version, the old version does not support

这是一款osu的铺面批量下载器，可以从ppy搜索爬取指定数量的图并进行下载

It is an osu pavement batch downloader. It can get a specifies quantity of beatmaps fit your filter.

### 现在支持的参数 (support parameters)

|参数名 (parameter name)|描述 (description)|
|--|--|
|general|官方搜索参数 (official parameter)|
|mode|官方搜索参数 (official parameter)|
|categories|官方搜索参数 铺面状态 (official parameter, map status)|
|explicit_content|官方搜索参数 18+ (official parameter, nsfw)|
|genre|官方搜索参数 (official parameter)|
|language|官方搜索参数 (official parameter)|
|extra|官方搜索参数 (official parameter)|
|rank_achieved|官方搜索参数,仅支持撒泼特 (official parameter, supporter only)|
|played|官方搜索参数,仅支持撒泼特 (official parameter, supporter only)|
|created|铺面创建时间 (beatmapset's create date)|
|ranked|铺面被认可的时间，或者说拥有排行榜的时间 (date that beatmapset get ranked(have leaderboard))|
|star|不解释 (will not explain)|
|ar|不解释 (will not explain)|
|od|不解释 (will not explain)|
|cs|不解释 (will not explain)|
|hp|不解释 (will not explain)|
|length|不解释 (will not explain)|
|bpm|不解释 (will not explain)|

# 怎么使用(How-to-use)

下载python脚本，切到python3.8并安装requirements.txt中的依赖

Download this repo and switch to python3.8 and `pip install -r requirements.txt1`

或者直接在`AllReleases`文件夹内下载打包好的程序

Or you can download release applicatoin in `AllReleases` folder.

#### 第一次使用 (First use)

首先打开一次程序，生成`config.json`，对`config.json`内进行更改，再次打开程序即可。建议使用网页版json编辑器进行编辑。

First open the application to generate the `config.json`. Change content in `config.json` and then open the application again. It is recommended to use web json editor for editing `config.json`.

最后打开 [osu网页的设置界面](https://osu.ppy.sh/home/account/edit) 删除名为`()`的客户端。

Finally open [settings](https://osu.ppy.sh/home/account/edit) and end session named `()`。

#### 更新 (Update)

删除所有东西，重新搞

Delete all and use it as the first time.

#### tips:

- 使用ranked参数之后，即使没有指定铺面状态，也只会出现loved和ranked铺面
- When use parameter ranked. Even if you didnt specify the status of map, there will be only loved and ranked.
- 建议created和ranked参数二选一进行使用
- Suggests to choose one between `created` and `ranked`. Avoid to use them at the same time.
- 如果为`null`，那么这个参数将被忽略
- If some value is `null`, it will be ignored
- 目前没有支持小夜镜像站，请把镜像改为`official`
- Dont support sayobot mirror now. Please change mirror to `official`

# 详细的参数解释 (Detailed parameters)

|参数名 (parameter name)|是否可以拼接以及其参数 (Whether can be spliced and its parameters)|
|--|--|
|以下为官方参数(official parameters below)|可以在[搜索页面](https://osu.ppy.sh/beatmapsets)的搜索框下查看 (Can be viewed in [map search page](https://osu.ppy.sh/beatmapsets) )|
|general|Y   recommended(推荐难度) converts(包括转铺) follows(已关注铺师) spotlights(聚光灯) featured_artists(精选艺术家)|
|mode|N   0=std 1=taiko 2=catch 3=mania|
|categories|N   any {留空(blank)}(计入排名) ranked qualified loved favourites(收藏夹) pending wip(制作中) graveyard mine(我的)|
|explicit_content|N   布尔值(bool value)|
|genre|N 1=未指定(Unspecified) 2=电子游戏(video game) 3=动漫(anime) 4=摇滚(rock) 5=流行乐(pop) 6=其他(other) 7=新奇(Novelty) 9=嘻哈(Hip Hop) 10=电子(electronic) 11=金属(Metal) 12=古典(Classical) 13=民谣(Folk) 14=爵士(jazz)|
|language|N   1=未指定(Unspecified) 2=English 3=Japanese 4=Chinese 5=Instrumental 6=Korean 7=French 8=Germany 9=Swedish 10=Spanish 11=Italian 12=Russian 13=Polish 14=others|
|extra|Y   video storyboard|
|rank_achieved|Y   XH X SH S A B C D|
|played|N   played unplayed|
|下方为自定义搜索参数(custom serch parameters below)||
|created|时间格式，看下面 (Time format, see below)|
|ranked|时间格式，看下面 (Time format, see below)|
|star|不解释 (will not explain)|
|ar|不解释 (will not explain)|
|od|不解释 (will not explain)|
|cs|不解释 (will not explain)|
|hp|不解释 (will not explain)|
|length|不解释 (will not explain)|
|bpm|不解释 (will not explain)|
|下方为其他参数 (other parameters below)||
|count|下载数量 (Download number)|
|mirror|镜像站，支持"official" "sayobot" (download mirror, now support "official" and "sayobot")|
|download_sem|下载并发数 (Download concurrent)|

可以拼接的参数之间使用英文句号进行拼接

The spliced-able parameters used `.` to splice

例如general参数可以为`"recommended.spotlights"`

Such as parameter general can be `"recommended.spotlights"`

#### 时间格式

以下时间格式均可使用

|格式|输入示例|开始时间|结束时间|提示|
|--|--|--|--|--|
|y|2000|2000-01-01 00:00:00 +00:00|2001-01-01 00:00:00 +00:00 (也就是一年)||
|y-m|2000-01|2000-01-01 00:00:00 +00:00|2000-02-01 00:00:00 +00:00 (一个月)||
|y-m-d|2000-01-01|2000-01-01 00:00:00 +00:00|2000-01-02 00:00:00 +00:00 (一天)||
|任何有效的时间|2000-01-01 00:00:00 +00:00|2000-01-01 00:00:00 +00:00|2000-01-01 00:00:01 +00:00 (一秒)|奇怪的事情就像“一个月前还支持”。精确搜索(=)还是只有很短的范围内搜索虽然可能没有用处。（未经过翻译，但不推荐使用这种时间格式）|

- 时区默认为格林尼治时间 (时区只能被上表的第四种格式指定)
- 分隔符`-`  `.`  `/`  `不填`都是被支持的  `2020-11`, `2020/11`, `2020.11`, `202011` 都是有效的时间
- 开头的0是可选项 （202011 永远是 2020-11 而永远不会是 2020-01-01）（相似的 2020111 将会永远是 2020-11-01）
- 可以超过标准日期范围 （ 2000-13-01 会代表 2001-01-01）
- 年份必须是四位数

|操作符|代表的实际比较|
|--|--|
|`=`|`startTime >= x > endTime`|
|`>`|`x >= endTime`|
|`<`|`x < startTime`|
|`>=`|`x >= startTime`|
|`<=`|`x < startTime`|

参考[该页面](https://github.com/ppy/osu-web/pull/7358)进行翻译解释

#### **English version see [here](https://github.com/ppy/osu-web/pull/7358#issue-837704534)**

# 一个配置文件的例子 (a config.json example)

标准的json格式不允许注释的存在，所以记得删掉

Standard json did not allow annotation. So please remove after copy

```json
{
    "api": {
        "api_v2_client_id": 6322,
        "api_v2_client_secret": "G5Dpfd1hAgAt8zkt0aFklV8bteaZITv1vC2bxcf",
        "username": "wanna accuracy",
        "password": "balabalabalabala"
    },
    "official": {
        "general": null,
        "mode": 0,
        "categories": "any",
        "explicit_content": true,
        "genre": null,
        "language": 3,
        "extra": "video.storyboard",
        "rank_achieved": null,
        "played": null
    },
    "search": {
        "created": {
            "min": 20180101,
            "max": 20210101,
            "eq": true
        },
        "ranked": {
            "min": null,
            "max": null,
            "eq": true
        },
        "star": {
            "min": 6,
            "max": 8,
            "eq": true
        },
        "ar": {
            "min": 9,
            "max": null,
            "eq": true
        },
        "od": {
            "min": null,
            "max": null,
            "eq": true
        },
        "cs": {
            "min": 4,
            "max": 6,
            "eq": true
        },
        "hp": {
            "min": null,
            "max": null,
            "eq": true
        },
        "length": {
            "min": null,
            "max": null,
            "eq": true
        },
        "bpm": {
          "min": null,
          "max": null,
          "eq": true
        }
    },
    "other": {
        "count": 200,
        "mirror": "official",
        "download_sem": 5
    }
}
```
