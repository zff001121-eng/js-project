# -*- coding: utf-8 -*-
"""
百度贴吧帖子列表接口 page_pc 纯协议请求脚本
================================================
目标接口: POST https://tieba.baidu.com/c/f/frs/page_pc
返回数据: 贴吧帖子列表 (标题/作者/摘要/图片等)

核心还原结论:
  1. sign 参数 = MD5( 排序后的 "k=v" 拼接串 + 密钥 "tiebaclient!!!" )
     - 参与签名的参数必须包含 kw / pn / rn / tbs (tbs 缺一不可)
  2. tbs 参数 = 反 CSRF 令牌, 从接口 https://tieba.baidu.com/dc/common/tbs 获取
  3. Cookie   = 首次访问 www.baidu.com 拿到 BAIDUID/BIDUPSID/PSTM,
                再访问 tbs 接口拿到 tbs cookie, 由 http.cookiejar 自动维护

依赖: 仅 Python 标准库 (urllib / http.cookiejar / hashlib / json / gzip)
注意: 本机 `requests` 库存在 SSL 握手超时问题, 故采用 stdlib urllib(直连, 无需代理)
"""

import sys
import json
import gzip
import hashlib
import urllib.request
import urllib.parse
import http.cookiejar

# Windows 控制台默认 GBK, 强制 UTF-8 输出以正确显示中文/emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

BASE = "https://tieba.baidu.com"
FRS_REFERER = "https://tieba.baidu.com/f"

# 贴吧签名密钥 (多年稳定的公开密钥)
SIGN_SECRET = "tiebaclient!!!"


class TiebaPagePc:
    def __init__(self):
        cj = http.cookiejar.CookieJar()
        # 直连 (不经过系统代理); 如需要代理, 把 ProxyHandler({}) 换成 ProxyHandler({"https": "http://127.0.0.1:7897"})
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPCookieProcessor(cj),
        )
        self.cj = cj

    def _request(self, method, url, data=None, referer=FRS_REFERER):
        headers = {
            "User-Agent": UA,
            "Referer": referer,
            "Accept-Encoding": "gzip",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }
        body = None
        if data is not None:
            body = urllib.parse.urlencode(data).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        resp = self.opener.open(req, timeout=20)
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return resp.status, raw

    def get(self, url, referer=FRS_REFERER):
        return self._request("GET", url, None, referer)

    def post(self, url, data, referer=FRS_REFERER):
        return self._request("POST", url, data, referer)

    def init_session(self):
        """建立会话: 拿 BAIDUID/BIDUPSID/PSTM 等基础 cookie"""
        self.get("https://www.baidu.com/", referer="https://www.baidu.com/")

    def get_tbs(self):
        """获取反 CSRF 令牌 tbs"""
        _, raw = self.get(f"{BASE}/dc/common/tbs")
        return json.loads(raw.decode("utf-8"))["tbs"]

    @staticmethod
    def sign(params: dict) -> str:
        """贴吧 sign: MD5(排序拼接 + 密钥)"""
        raw = "".join(f"{k}={params[k]}" for k in sorted(params)) + SIGN_SECRET
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def fetch_threads(self, kw: str, pn: int = 1, rn: int = 30):
        """请求 page_pc 接口, 返回 (http_status, 完整响应 dict)"""
        tbs = self.get_tbs()
        params = {"kw": kw, "pn": str(pn), "rn": str(rn), "tbs": tbs}
        params["sign"] = self.sign(params)

        status, raw = self.post(f"{BASE}/c/f/frs/page_pc", params,
                                referer=f"{FRS_REFERER}?kw={urllib.parse.quote(kw)}&fr=home")
        return status, json.loads(raw.decode("utf-8"))


def _concat_text(obj):
    """拼接一个组件内所有分段文本 (data[].text_info.text / data[].text.text)

    贴吧新版标题可能分多段: type=6 是带颜色标签(如「求助」), type=1 是正文,
    需按顺序拼接才是完整标题。
    """
    parts = []

    def walk(o):
        if isinstance(o, dict):
            ti = o.get("text_info")
            if isinstance(ti, dict):
                t = ti.get("text")
                if isinstance(t, str) and t:
                    parts.append(t)
                return  # text_info 已处理, 不再向下走, 避免重复计数
            if isinstance(o.get("text"), str) and o["text"]:
                parts.append(o["text"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(obj)
    return "".join(parts)


def _title_text(feed_title_obj):
    """标题 = 拼接 data[] 中所有 type=1 段的 text_info.text

    type=6 是带颜色的「求助」等标签, 不是标题正文, 需排除。
    """
    data = feed_title_obj.get("data", [])
    parts = []
    for d in data:
        if isinstance(d, dict) and d.get("type") == 1:
            ti = d.get("text_info", {})
            if isinstance(ti, dict) and isinstance(ti.get("text"), str):
                parts.append(ti["text"])
    return "".join(parts)


def extract_threads(data: dict):
    """从新版 page_pc 响应结构中提取帖子列表 (标题/作者/摘要)

    新版结构: page_data.feed_list[].feed.components[] 中
      - feed_head.main_data[].text.text       -> 作者
      - feed_title.data[].text_info.text      -> 标题 (type=1 段)
      - feed_abstract.data[].text_info.text   -> 摘要
    """
    feed_list = data.get("page_data", {}).get("feed_list", [])
    threads = []
    for item in feed_list:
        feed = item.get("feed")
        if not feed:
            continue
        title = author = abstract = ""
        for comp in feed.get("components", []):
            ctype = comp.get("component")
            if ctype == "feed_head":
                author = _concat_text(comp.get("feed_head", {}).get("main_data"))
            elif ctype == "feed_title":
                title = _title_text(comp.get("feed_title", {}))
            elif ctype == "feed_abstract":
                abstract = _concat_text(comp.get("feed_abstract", {}))
        threads.append({"title": title, "author": author, "abstract": abstract})
    return threads


def main():
    import argparse
    parser = argparse.ArgumentParser(description="百度贴吧 page_pc 接口请求")
    parser.add_argument("kw", nargs="?", default="植物吧", help="贴吧名称")
    parser.add_argument("--pn", type=int, default=1, help="页码 (1 起)")
    parser.add_argument("--rn", type=int, default=30, help="每页数量")
    args = parser.parse_args()

    client = TiebaPagePc()
    client.init_session()
    status, data = client.fetch_threads(args.kw, args.pn, args.rn)

    print(f"HTTP status = {status}")
    print(f"error_code  = {data.get('error_code')}")
    forum = data.get("forum", {})
    page = data.get("page", {})
    print(f"贴吧: {forum.get('name')}  会员:{forum.get('member_num')}  帖子总数:{forum.get('thread_num')}")
    print(f"页码: {page.get('current_page')}/{page.get('total_page')}  每页:{page.get('page_size')}")

    threads = extract_threads(data)
    print(f"\n本页帖子数: {len(threads)}")
    for i, t in enumerate(threads, 1):
        print(f"  {i:>2}. [{t['author']}] {t['title']}")


if __name__ == "__main__":
    main()
