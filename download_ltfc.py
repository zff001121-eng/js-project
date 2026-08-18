# -*- coding: utf-8 -*-
"""
中华珍宝馆 (g2.ltfc.net) 高清图下载脚本
=======================================

使用 requests 下载并拼接「高清大图」（非缩略图）。

原理
----
1. 请求作品页 HTML，解析出每一页的 resourceId / 原始尺寸 / maxlevel。
2. 高清图以 512x512 瓦片(tile)的形式存放在 CDN (cag-ac.ltfc.net)：
       https://cag-ac.ltfc.net/cagstore/{resourceId}/{level}/{x}_{y}.jpg
   CDN 鉴权参数 auth_key 由前端用 md5 计算得到：
       auth_key = md5("{path}-{expires}-0-0-ltfcdotnet")
       其中 path = /cagstore/{resourceId}/{level}/{x}_{y}.jpg
3. 下载该级别下所有瓦片，再用 PIL 拼接为一张完整高清图。

用法
----
    python download_ltfc.py

参数说明（文件顶部常量）：
    PAGE_URL     作品页地址
    LEVEL        下载级别。None 表示使用 maxlevel（最高清/原图分辨率）。
                 若想得到较小的高清图可填 16 / 17（数字越小分辨率越低）：
                     level 18 -> 原图（约 10500 x 23500，每张约 250 百万像素）
                     level 17 -> 约 5200 x 11800
                     level 16 -> 约 2600 x 5900
                     level 15 -> 约 1300 x 2900
"""

import math
import os
import re
import struct
import time
import hashlib

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------- 配置 ----------------------
PAGE_URL = "https://g2.ltfc.net/view/SUFA/67dd6df16c96742943b9bad8?originType=SUFA_PAGE"
OUTPUT_DIR = "高清图"
LEVEL = None          # None = 最高清（原图分辨率）；或填 15~18
TILE_SIZE = 512       # 瓦片尺寸
CDN_HOST = "https://cag-ac.ltfc.net"
SECRET = "ltfcdotnet"     # CDN 鉴权密钥（前端硬编码）
CONCURRENCY = 16      # 并发下载线程数
JPEG_QUALITY = 95     # 输出 JPEG 质量
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://g2.ltfc.net/",
}
# --------------------------------------------------


def fetch_html(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_images(html):
    """从页面 HTML 的 SSR 数据里解析出每张图的信息。"""
    names = re.findall(r'\\"name\\":\\"([^\\"]*)\\","resourceId\\"', html)
    rids = re.findall(r'\\"resourceId\\":\\"([0-9a-f]{24})\\"', html)
    sizes = [
        (int(w), int(h))
        for w, h in re.findall(r'\\"size\\":\{\\"width\\":(\d+),\\"height\\":(\d+)\}', html)
        if int(w) > 0
    ]
    maxlevels = [int(x) for x in re.findall(r'\\"maxlevel\\":(\d+)', html)]

    n = len(rids)
    images = []
    for i in range(n):
        name = names[i] if i < len(names) else f"第{i + 1}页"
        width, height = sizes[i] if i < len(sizes) else (0, 0)
        maxlevel = maxlevels[i] if i < len(maxlevels) else 18
        images.append({
            "name": name,
            "resourceId": rids[i],
            "width": width,
            "height": height,
            "maxlevel": maxlevel,
        })
    return images


def tile_url(resource_id, level, x, y):
    """生成带 auth_key 的瓦片 URL。"""
    path = f"/cagstore/{resource_id}/{level}/{x}_{y}.jpg"
    expires = int(time.time()) + 300  # 5 分钟后过期，保证本次下载期间有效
    digest = hashlib.md5(f"{path}-{expires}-0-0-{SECRET}".encode()).hexdigest()
    return f"{CDN_HOST}{path}?auth_key={expires}-0-0-{digest}"


def jpeg_size(data):
    """解析 JPEG 字节流，返回 (width, height)。"""
    i = 2
    while i < len(data) - 4:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h = struct.unpack(">H", data[i + 5:i + 7])[0]
            w = struct.unpack(">H", data[i + 7:i + 9])[0]
            return w, h
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
        else:
            length = struct.unpack(">H", data[i + 2:i + 4])[0]
            i += 2 + length
    return TILE_SIZE, TILE_SIZE


def download_tile(session, resource_id, level, x, y):
    """下载单个瓦片，返回 (x, y, bytes)。"""
    url = tile_url(resource_id, level, x, y)
    for attempt in range(3):
        try:
            r = session.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return x, y, r.content
        except requests.RequestException:
            pass
        time.sleep(0.5 * (attempt + 1))
    return x, y, None


def download_and_stitch(session, img, level, out_path):
    from PIL import Image
    from io import BytesIO

    rid = img["resourceId"]
    width = img["width"]
    height = img["height"]
    maxlevel = img["maxlevel"]
    level = level if level is not None else maxlevel
    downscale = 2 ** (maxlevel - level)

    nx = math.ceil(width / (TILE_SIZE * downscale))
    ny = math.ceil(height / (TILE_SIZE * downscale))
    total = nx * ny

    tiles = {}
    coords = [(x, y) for y in range(ny) for x in range(nx)]
    failed = []

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {
            pool.submit(download_tile, session, rid, level, x, y): (x, y)
            for x, y in coords
        }
        done = 0
        for fut in as_completed(futures):
            x, y, content = fut.result()
            done += 1
            if content is None:
                failed.append((x, y))
                continue
            tiles[(x, y)] = content
            if done % 200 == 0 or done == total:
                print(f"    [{img['name']}] {done}/{total} 瓦片")
        # 重试失败的瓦片
        for x, y in failed:
            _, _, content = download_tile(session, rid, level, x, y)
            if content is None:
                raise RuntimeError(f"瓦片 {level}/{x}_{y} 下载失败")
            tiles[(x, y)] = content

    # 根据边缘瓦片实际尺寸确定画布大小
    first_col = jpeg_size(tiles[(nx - 1, 0)])[0]
    first_row = jpeg_size(tiles[(0, ny - 1)])[1]
    canvas_w = (nx - 1) * TILE_SIZE + first_col
    canvas_h = (ny - 1) * TILE_SIZE + first_row

    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    for (x, y), content in tiles.items():
        tile_img = Image.open(BytesIO(content)).convert("RGB")
        canvas.paste(tile_img, (x * TILE_SIZE, y * TILE_SIZE))

    canvas.save(out_path, "JPEG", quality=JPEG_QUALITY)
    print(f"    已保存: {out_path}  ({canvas_w}x{canvas_h})")


def main():
    print(f"获取页面: {PAGE_URL}")
    html = fetch_html(PAGE_URL)
    images = parse_images(html)
    print(f"共解析到 {len(images)} 张高清图\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    session = requests.Session()

    for i, img in enumerate(images, start=1):
        level = LEVEL if LEVEL is not None else img["maxlevel"]
        print(f"[{i}/{len(images)}] {img['name']}  原图 {img['width']}x{img['height']}  "
              f"下载级别 {level}")
        out_path = os.path.join(OUTPUT_DIR, f"{i:02d}_{img['name']}.jpg")
        download_and_stitch(session, img, level, out_path)

    print("\n全部完成！输出目录:", os.path.abspath(OUTPUT_DIR))


if __name__ == "__main__":
    main()
