# -*- coding: utf-8 -*-
"""
LTFCClient —— 带 token 复用与轮换的客户端封装

Token 生命周期结论（由前端 l()/b() 源码 + 实测得出）：
    - token（cag.tid）缓存复用，有效期 expireAfter=2592000 秒 ≈ 30 天，过期才重新获取
    - tdid（设备 id）与 token 解耦，可长期复用，换 token 无需重新注册设备
    - 因此：一个 token 可打多次请求；打够 N 次后换个新 token 继续，完全可行

用法：
    c = LTFCClient(auto_rotate_after=10)   # 每 10 次自动换 token
    for page in range(100):
        r = c.search_overview(page_skip=page*24)
        ...
"""

import requests

from js_.珍宝馆.main import get_cag_tid
from js_.珍宝馆.search_overview import register_device, search_overview


class LTFCClient:
    def __init__(self, auto_rotate_after: int = 0):
        """
        auto_rotate_after: 每打多少次请求自动换一次 token（0 = 不自动换，手动调 rotate_token）。
        """
        self.session = requests.Session()
        self.token: str | None = None
        self.tdid: str = ""
        self.auto_rotate_after = auto_rotate_after
        self._requests_since_rotate = 0
        self._total_requests = 0

    # ---- 初始化 / 轮换 ----

    def init(self, register: bool = True) -> "LTFCClient":
        """生成 token（并按需注册设备拿 tdid）。"""
        self.token = get_cag_tid(self.session)["cag.tid"]
        if register:
            self.tdid = register_device(self.session, self.token)
        self._requests_since_rotate = 0
        return self

    def rotate_token(self, re_register: bool = False) -> str:
        """换一个新 token。默认保留现有 tdid（实测 tdid 与 token 解耦）。"""
        self.token = get_cag_tid(self.session)["cag.tid"]
        if re_register or not self.tdid:
            self.tdid = register_device(self.session, self.token)
        self._requests_since_rotate = 0
        return self.token

    # ---- 业务请求 ----

    def search_overview(
        self,
        keyword: str = "",
        categories=None,
        page_skip: int = 0,
        page_limit: int = 24,
    ) -> dict:
        """复用当前 token + tdid 请求 searchOverview；达到阈值自动换 token。"""
        self._maybe_rotate()
        if self.token is None:
            self.init()
        result = search_overview(
            self.session, self.token, self.tdid,
            keyword=keyword, categories=categories,
            page_skip=page_skip, page_limit=page_limit,
        )
        self._requests_since_rotate += 1
        self._total_requests += 1
        return result

    def _maybe_rotate(self) -> None:
        if (
            self.auto_rotate_after > 0
            and self.token is not None
            and self._requests_since_rotate >= self.auto_rotate_after
        ):
            self.rotate_token()


if __name__ == "__main__":
    # 演示：每 3 次自动换 token，共打 8 次
    c = LTFCClient(auto_rotate_after=3).init()

    for i in range(1, 9):
        r = c.search_overview()
        print(
            f"第{i:2d}次 | token={c.token[:16]}... "
            f"本token已用{c._requests_since_rotate}次 | total={r.get('total')}"
        )
