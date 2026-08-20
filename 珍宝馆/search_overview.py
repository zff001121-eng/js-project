# -*- coding: utf-8 -*-
"""
请求 https://api.quanku.art/cag2.AIRecommendation/searchOverview

完整链路（对应前端 LJ() 通用请求封装）：
    1. 生成游客 token（cag.tid）  —— 见 main.py
    2. registerDevice 注册设备拿到 tdid
    3. searchOverview 携带 token + context 发起搜索

前端所有走 api.quanku.art 的业务请求，body 里都会被自动注入：
    token                 = cag.tid（游客令牌）
    context.tourToken     = cag.tid
    context.appKey        = "CAGWEB"
    context.appSec        = "ZETYK0B8KTQB41KYWA2"
    context.tdid          = 设备 id
    context.appVersion    = ""
"""

import json

import requests

from js_.珍宝馆.main import DEFAULT_UA, get_cag_tid

API_HOST = "https://api.quanku.art"
APP_KEY = "CAGWEB"
APP_SEC = "ZETYK0B8KTQB41KYWA2"

# 前端 fetch 用 body: JSON.stringify(...) 且未显式设置 Content-Type，
# 浏览器默认补成 text/plain;charset=UTF-8
HEADERS = {
    "Accept": "*/*",
    "Content-Type": "text/plain;charset=UTF-8",
    "Origin": "https://g2.ltfc.net",
    "Referer": "https://g2.ltfc.net/",
    "User-Agent": DEFAULT_UA,
}


def _post(session: requests.Session, path: str, body: dict) -> dict:
    """按前端 LJ() 的方式发 POST（text/plain + JSON 字符串 body）。"""
    resp = session.post(
        f"{API_HOST}{path}",
        headers=HEADERS,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def _context(token: str, tdid: str = "", app_key: str = APP_KEY, app_sec: str = APP_SEC) -> dict:
    return {
        "tourToken": token,
        "appKey": app_key,
        "appSec": app_sec,
        "tdid": tdid,
        "appVersion": "",
    }


def register_device(session: requests.Session, token: str) -> str:
    """注册设备，返回 tdid。"""
    body = {
        "registerInfo": {
            "type": "MONITOR",
            "brand": "unknown",
            "deviceName": "unknown浏览器",
            "pixSize": {"width": 1038, "height": 907},
        },
        "token": token,
        "context": _context(token),
    }
    data = _post(session, "/cag2.TouristDeviceService/registerDevice", body)
    return data.get("tdid", "")


def search_overview(
    session: requests.Session,
    token: str,
    tdid: str = "",
    keyword: str = "",
    categories=None,
    page_skip: int = 0,
    page_limit: int = 24,
) -> dict:
    """请求 searchOverview，返回完整 JSON 结果。

    categories 默认 ["SUFA"]，与页面 URL 的 searchType=SUFA 对应。
    """
    body = {
        "page": {"skip": page_skip, "limit": page_limit},
        "keyword": keyword,
        "categories": categories or ["SUFA"],
        "filters": [],
        "token": token,
        "context": _context(token, tdid),
    }
    return _post(session, "/cag2.AIRecommendation/searchOverview", body)


if __name__ == "__main__":
    sess = requests.Session()

    # 1. 生成 token
    token = get_cag_tid(sess)["cag.tid"]
    print("token:", token)

    # 2. 注册设备拿 tdid
    tdid = register_device(sess, token)
    print("tdid :", tdid)

    # 3. 请求 searchOverview
    result = search_overview(sess, token, tdid)
    # print(result)
    print("\nsearchOverview 成功！")
    print("total        :", result.get("total"))
    print("sort         :", result.get("sort"))
    print("返回顶层字段   :", list(result.keys()))
    # 打印少量样本数据
    for k in ("list", "data", "items", "result"):
        if k in result and isinstance(result[k], list) and result[k]:
            print(f"\n样本({k})[0]:", json.dumps(result[k][0], ensure_ascii=False)[:500])
            break
