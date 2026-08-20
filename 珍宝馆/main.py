# -*- coding: utf-8 -*-
"""
生成 g2.ltfc.net 的 cag.tid Cookie
==================================

结论：cag.tid 的值【不是】前端本地加密生成的，而是由 Next.js 服务端的
React Server Action 动态下发的游客令牌（tourist token），每次调用都会返回一个
全新的随机值。

前端那段代码（async function l(){...}）只是「取缓存 / 调服务端 / 写 Cookie」的
封装，真正的入口是：
    o.hP()  =>  $("510d40750b93bbb35d0a2910b3268b2803a94354")
    $() 是 React 的 createServerReference，最终向服务端发一个
    POST 请求（Next-Action 头标识动作），服务端返回 { token, expireAfter }。

因此 Python 实现只需复刻这个 Server Action 请求：
    POST https://g2.ltfc.net/search?searchType=SUFA&curTab=SUFA
    Headers:
        Accept:       text/x-component
        Content-Type: text/plain;charset=UTF-8
        Next-Action:  510d40750b93bbb35d0a2910b3268b2803a94354
        Origin:       https://g2.ltfc.net
        Referer:      https://g2.ltfc.net/search?searchType=SUFA&curTab=SUFA
    Body: []
    响应为 React Flight(RSC) 文本格式，token 在 "1:" 行。

Cookie 写入规则（对应前端 m() 函数）：
    cag.tid        = token
    cag.tid.expire = Date.now() + expireAfter * 1000   （expireAfter 单位为秒）
"""

import json
import re
import time

import requests

# ---- 常量 ----
SEARCH_URL = "https://g2.ltfc.net/search"
SEARCH_PARAMS = {"searchType": "SUFA", "curTab": "SUFA"}
NEXT_ACTION_ID = "510d40750b93bbb35d0a2910b3268b2803a94354"
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)

# 默认过期秒数（前端 b() 函数里，cookie 无 expire 时的兜底值 = 31536000 秒 = 1 年）
FALLBACK_EXPIRE_SECONDS = 31536000


def fetch_tourist_token(session: requests.Session | None = None) -> dict:
    """调用 Server Action，返回 {"token": str, "expireAfter": str/int}。

    expireAfter 为服务端下发的过期时长（秒）。该值通常固定为 2592000（30 天）。
    """
    sess = session or requests.Session()
    headers = {
        "Accept": "text/x-component",
        "Content-Type": "text/plain;charset=UTF-8",
        "Next-Action": NEXT_ACTION_ID,
        "Origin": "https://g2.ltfc.net",
        "Referer": "https://g2.ltfc.net/search?searchType=SUFA&curTab=SUFA",
        "User-Agent": DEFAULT_UA,
    }
    resp = sess.post(SEARCH_URL, params=SEARCH_PARAMS, headers=headers, data="[]", timeout=15)
    resp.raise_for_status()
    return parse_flight_result(resp.text)


def parse_flight_result(body: str) -> dict:
    """从 React Flight(RSC) 文本里解析 Server Action 的返回值。

    响应形如：
        0:["$@1",["SGU7h02KQj2wghW9aneZN",null]]
        1:{"token":"aocJ...==.t","expireAfter":"2592000"}

    返回值为带 "1:" 前缀的那一行（数字前缀是 Flight 行号）。
    """
    for line in body.splitlines():
        line = line.strip()
        m = re.match(r"^(\d+):(.*)$", line)
        if not m:
            continue
        payload = m.group(2)
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "token" in data and "expireAfter" in data:
            return data
    raise ValueError("未在响应中解析到 {token, expireAfter}，原文：\n%s" % body)


def build_cag_tid_cookie(token: str, expire_after=None) -> dict:
    """按前端 m() 的规则计算最终 Cookie 字段。

    返回 {"cag.tid": token, "cag.tid.expire": <毫秒时间戳字符串>}
    """
    if expire_after is None:
        expire_after = FALLBACK_EXPIRE_SECONDS
    expire_after = int(expire_after)
    if expire_after <= 0:
        expire_after = FALLBACK_EXPIRE_SECONDS
    # 前端：new Date().getTime() + 1000 * expireAfter
    expire_ms = int(time.time() * 1000) + expire_after * 1000
    return {
        "cag.tid": token,
        "cag.tid.expire": str(expire_ms),
    }


def get_cag_tid(session: requests.Session | None = None) -> dict:
    """一步到位：生成 cag.tid 及其过期字段。"""
    data = fetch_tourist_token(session)
    return build_cag_tid_cookie(data["token"], data["expireAfter"])


if __name__ == "__main__":
    sess = requests.Session()
    cookie_fields = get_cag_tid(sess)
    print(json.dumps(cookie_fields, ensure_ascii=False, indent=2))

    # 附带打印可直接塞进请求头的 Cookie 串
    cookie_str = "; ".join(f"{k}={v}" for k, v in cookie_fields.items())
    print("\nCookie 串：")
    print(cookie_str)
