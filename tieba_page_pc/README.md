# 百度贴吧 page_pc 接口逆向（纯协议请求）

目标：完整请求 `https://tieba.baidu.com/c/f/frs/page_pc` 接口，返回 HTTP 200 并拿到帖子列表数据。

## 结论速览

| 项 | 结论 |
|---|---|
| 接口 | `POST https://tieba.baidu.com/c/f/frs/page_pc` |
| 响应 | HTTP 200，UTF-8 JSON（gzip 压缩），`error_code = 0` |
| `tbs` | 反 CSRF 令牌，从 `GET https://tieba.baidu.com/dc/common/tbs` 获取（返回 `{"tbs":"...","is_login":0}`） |
| `sign` | `MD5( 排序后 "k=v" 拼接串 + "tiebaclient!!!" )`，参与签名参数含 `kw/pn/rn/tbs` |
| Cookie | 访问 `www.baidu.com` 拿 `BAIDUID/BIDUPSID/PSTM`，`tbs` 接口会再写 `tbs` cookie，由 `http.cookiejar` 自动维护 |

## 签名算法（关键）

```python
import hashlib

def sign(params: dict) -> str:
    raw = "".join(f"{k}={params[k]}" for k in sorted(params)) + "tiebaclient!!!"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()
```

**踩坑点：`tbs` 必须参与 sign 计算。** 不含 `tbs` 时返回 `error_code 110001`（签名错误）。

## 请求参数

```python
params = {
    "kw": "植物吧",   # 贴吧名
    "pn": "1",        # 页码（1 起）
    "rn": "30",       # 每页数量
    "tbs": tbs,       # 反 CSRF 令牌
}
params["sign"] = sign(params)  # 最后加 sign
```

## 响应结构（新版）

帖子列表在新版响应中已不在顶层 `thread_list`，而是：

```
page_data.feed_list[].feed.components[]
├── feed_head     -> main_data[].text.text       (作者)
├── feed_title    -> data[].text_info.text       (标题；type=1 是正文，type=6 是「求助」彩色标签)
├── feed_abstract -> data[].text_info.text       (摘要)
├── feed_pic      -> 图片
└── feed_social   -> 点赞/回复等社交信息
```

## 运行

```bash
python main.py 植物吧            # 第 1 页
python main.py 植物吧 --pn 2     # 第 2 页
python main.py 植物吧 --pn 1 --rn 50
```

依赖：**仅 Python 标准库**（`urllib` / `http.cookiejar` / `hashlib` / `json` / `gzip`），无第三方依赖。

## 网络注意点

- 本机 `requests` 库存在 SSL 握手超时问题（`ReadTimeout`），`urllib` / `http.client` / `curl` 均正常，故采用 stdlib `urllib`。
- 默认**直连**（`ProxyHandler({})`）。如需走代理，把 `ProxyHandler({})` 换成 `ProxyHandler({"https": "http://127.0.0.1:7897"})`。
- 直连与代理均实测可用（curl 0.3s / 0.07s）。

## 授权说明

本脚本用于自有/授权平台的接口对接与数据获取，仅供学习与技术验证。
