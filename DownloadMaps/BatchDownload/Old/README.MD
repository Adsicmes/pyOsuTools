# 下载铺面
## 原理
扒ppy -> 筛选 -> 下载
## 使用参数
```json
{
    "params": {  //参考下方搜索用参数解释
        "c": null,
        "m": null,
        "s": null,
        "nsfw": null,
        "e": null,
        "r": null,
        "played": null,
        "l": null,
        "g": null
    },
    "api": {
        "v2": {  //这一栏是apiv2的填写
            "id": 114514,
            "secret": "Your secret"
        },
        "login": {  //这一栏是osu的登录，实现非寻常的api
            "username": "You osu username",
            "password": "Password here"
        }
    },
    //以下为过滤参数，是各项的最大最小值，全部符合区间范围就过，不一定都要改，看着来就行
    "total_length": {
        "min": 1,
        "max": 300
    },
    "ar": {
        "min": 0,
        "max": 10
    },
    "cs": {
        "min": 0,
        "max": 10
    },
    "od": {
        "min": 0,
        "max": 10
    },
    "hp": {
        "min": 0,
        "max": 10
    },
    "bpm": {
        "min": 0,
        "max": 1000
    },
    "star": {
        "min": 0,
        "max": 10
    },
    "count": 200,  //下载数量
    "sayo_mirror": true,  //是否尽量使用sayo下载，国内用户建议开启
    "sayo_sem": 10,  //sayo查询的最大并发数
    "download_sem": 10  //sayo下载的最大并发数(ppy有api限制，不采用高并发)
}
```
### 搜索用参数解释
played和r只能撒泼特使用  
以下参数组合使用'.'连接  
是否可以组合用 Y/N 表示  
:param c: Y recommended(推荐难度) converts(包括转铺) follows(已关注铺师) spotlights(聚光灯) featured_artists(精选艺术家)  
:param m: N 0=std 1=taiko 2=catch 3=mania  
:param s: N any 不填(默认为所有计入排名的图) ranked qualified loved favourites(收藏夹) pending wip(制作中) graveyard mine(我的)  
:param nsfw: N 十八禁内容  
:param e: Y video storyboard  
:param r: Y XH X SH S A B C D  
:param played: N played unplayed  
:param l: N 1=未指定 2=English 3=Japanese 4=Chinese 5=Instrumental 6=Korean 7=French 8=Germany  
 9=Swedish 10=Spanish 11=Italian 12=Russian 13=Polish 14=others  
:param g: N 1=未指定 2=电子游戏 3=动漫 4=摇滚 5=流行乐 6=其他 7=新奇 9=嘻哈 10=电子 11=金属 12=古典 13=民谣 14=爵士  

### 一个配置文件的例子
```json
{
    "params": {
        "c": null,
        "m": 0,
        "s": "ranked.loved.qualified",
        "nsfw": true,
        "e": null,
        "r": null,
        "played": null,
        "l": null,
        "g": null
    },
    "api": {
        "v2": {
            "id": 114514,
            "secret": "gwrbrb18d6g1v6d51v6e8f4s6ev1see45fw"
        },
        "login": {
            "username": "foo",
            "password": "foo"
        }
    },
    "total_length": {
        "min": 120,
        "max": 300
    },
    "ar": {
        "min": 9,
        "max": 10
    },
    "cs": {
        "min": 0,
        "max": 10
    },
    "od": {
        "min": 0,
        "max": 10
    },
    "hp": {
        "min": 0,
        "max": 10
    },
    "bpm": {
        "min": 0,
        "max": 1000
    },
    "star": {
        "min": 6,
        "max": 8
    },
    "count": 200,
    "sayo_mirror": true,
    "sayo_sem": 10,
    "download_sem": 10
}
```