"""
端到端验证脚本 v2:
1. 从 JD 搜索页获取新鲜 cookie
2. 用 Node 补环境生成 h5st
3. 用新鲜 cookie + h5st 请求 API
"""
import subprocess
import json
import urllib.parse
import urllib.request
import ssl
import http.cookiejar
import re
import time

ctx = ssl.create_default_context()

# ============================================================
# Step 1: 访问 JD 搜索页获取新鲜 cookies
# ============================================================
print("[1] 获取新鲜 cookies...")
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.HTTPCookieProcessor(cj)
)

search_url = "https://search.jd.com/Search?keyword=%E7%99%BD%E9%85%92&enc=utf-8"
req = urllib.request.Request(search_url)
req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
req.add_header("Accept-Language", "zh-CN,zh;q=0.9")

try:
    resp = opener.open(req, timeout=15)
    html = resp.read().decode('utf-8', errors='ignore')
    print(f"[1] 搜索页 HTTP {resp.getcode()}, 长度={len(html)}")
except Exception as e:
    print(f"[1] 搜索页请求失败: {e}")
    html = ""

# 合并 cookie
cookie_str = "; ".join(f"{c.name}={c.value}" for c in cj)
print(f"[1] Cookies: {cookie_str[:200]}...")

# 提取关键 cookie
def get_cookie(name):
    for c in cj:
        if c.name == name:
            return c.value
    return ""

__jdu = get_cookie("__jdu") or "17813333455121383673303"
print(f"[1] __jdu={__jdu}")

# ============================================================
# Step 2: 从 Node 生成 h5st
# ============================================================
print("\n[2] Node 生成 h5st...")
result = subprocess.run(
    ["node", "test_api.js"],
    cwd=r"D:\pythondata\Ai_coding\js_\h5st",
    capture_output=True, text=True, timeout=30
)

output = result.stdout
stderr_out = result.stderr
if stderr_out:
    print(f"[2] stderr: {stderr_out[:300]}")

json_start = output.find("---JSON_OUTPUT---")
if json_start == -1:
    print(f"[2] FAILED. Output: {output[-500:]}")
    exit(1)

data = json.loads(output[json_start + len("---JSON_OUTPUT---"):].strip())
h5st = data["h5st"]
t = data["t"]
body_str = data["body"]

print(f"[2] h5st: len={len(h5st)}, t={t}")
print(f"[2] h5st预览: {h5st[:120]}...")

# ============================================================
# Step 3: 用新鲜 cookie + 生成的 h5st 请求 API
# ============================================================
print("\n[3] 请求搜索 API...")

params = {
    "appid": "search-pc-java",
    "functionId": "pc_search_searchWare",
    "t": str(t),
    "client": "pc",
    "clientVersion": "1.0.0",
    "cthr": "1",
    "uuid": __jdu,
    "loginType": "3",
    "keyword": "白酒",
    "body": body_str,
    "h5st": h5st,
}

url = "https://api.m.jd.com/api?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
print(f"[3] URL 长度: {len(url)}")

req = urllib.request.Request(url)
req.add_header("Accept", "application/json, text/plain, */*")
req.add_header("Accept-Language", "zh-CN,zh;q=0.9")
req.add_header("Origin", "https://search.jd.com")
req.add_header("Referer", "https://search.jd.com/Search?keyword=%E7%99%BD%E9%85%92&enc=utf-8")
req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
req.add_header("x-referer-page", "https://search.jd.com/Search")
req.add_header("x-rp-client", "h5_2.1.0")
req.add_header("Cookie", cookie_str)

try:
    resp = opener.open(req, timeout=15)
    resp_body = resp.read().decode('utf-8')
    status = resp.getcode()
    print(f"[3] HTTP Status: {status}")
    print(f"[3] Response ({len(resp_body)} bytes):")

    try:
        resp_json = json.loads(resp_body)
        code = resp_json.get("code", "N/A")
        print(f"[3] API code: {code}")

        if code == "0" or code == 0:
            print("\n✅✅✅ 补环境验证成功! API 返回正常数据!")
            # 打印部分数据
            if "data" in resp_json:
                data_obj = resp_json["data"]
                if isinstance(data_obj, list) and len(data_obj) > 0:
                    first = data_obj[0]
                    print(f"[3] 搜索结果数: {len(data_obj)}")
                    print(f"[3] 第一条: {json.dumps(first, ensure_ascii=False)[:300]}")
        elif code == "403" or code == 403:
            print("\n⚠️ API 返回 403: 签名验证未通过")
            print(f"[3] 响应: {resp_body[:500]}")
        else:
            print(f"\n⚠️ API 返回 code={code}")
            print(f"[3] 响应: {resp_body[:500]}")

    except json.JSONDecodeError:
        print(f"[3] (非JSON): {resp_body[:500]}")

except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='ignore')
    print(f"[3] HTTP Error: {e.code}")
    print(f"[3] Body: {body[:500]}")
except Exception as e:
    print(f"[3] Exception: {type(e).__name__}: {e}")
