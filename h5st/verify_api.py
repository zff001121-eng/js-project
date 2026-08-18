"""
验证脚本: 使用 Node 生成的 h5st 请求 JD 搜索 API
依赖: pip install requests curl_cffi
"""
import subprocess
import json
from curl_cffi import requests

# ============================================================
# Step 1: 从 Node 获取 h5st
# ============================================================
print("[1] Node 生成 h5st...")
result = subprocess.run(
    ["node", "test_api.js"],
    cwd=r"D:\pythondata\Ai_coding\js_\h5st",
    capture_output=True, text=True, timeout=30
)

output = result.stdout
stderr_out = result.stderr
if stderr_out:
    for line in stderr_out.split('\n'):
        if 'DEP0169' not in line and line.strip():
            print(f"[stderr] {line[:200]}")

json_start = output.find("---JSON_OUTPUT---")
if json_start == -1:
    print(f"[1] FAILED. Output: {output[-500:]}")
    exit(1)

data = json.loads(output[json_start + len("---JSON_OUTPUT---"):].strip())
h5st = data["h5st"]
t = data["t"]
body_str = data["body"]

print(f"[1] h5st: len={len(h5st)}, t={t}")

# ============================================================
# Step 2: 构造请求
# ============================================================
print("\n[2] 构造请求...")

params = {
    "appid": "search-pc-java",
    "functionId": "pc_search_searchWare",
    "t": str(t),
    "client": "pc",
    "clientVersion": "1.0.0",
    "cthr": "1",
    "uuid": "17813333455121383673303",
    "loginType": "3",
    "keyword": "白酒",
    "body": body_str,
    "h5st": h5st,
}

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Origin": "https://search.jd.com",
    "Pragma": "no-cache",
    "Referer": "https://search.jd.com/Search?keyword=%E7%99%BD%E9%85%92&enc=utf-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "x-referer-page": "https://search.jd.com/Search",
    "x-rp-client": "h5_2.1.0",
}

cookies = {
    "shshshfpa": "f70fd7dc-7c56-5c72-3e17-abdeb153be26-1781193267",
    "__jdu": "17813333455121383673303",
    "jcap_dvzw_fp": "P_P8GlVOOEm144iM2FgmgZN8A4x9PwMIzoOOrB5nHwpacz0YC_mZcUioO4g8ID4Cu271Pw9huTM8bOCFVExaIAY_erM=",
    "pinId": "qGH5-p0r7oyOUI7O5LwVNw",
    "pin": "jd_aRgoSFvNvyvF",
    "unick": "jd_34wg5e69frc4y3",
    "_tp": "T6wqd%2FZUviRfRCtdjPjl9g%3D%3D",
    "_pst": "jd_aRgoSFvNvyvF",
    "shshshfpx": "f70fd7dc-7c56-5c72-3e17-abdeb153be26-1781193267",
    "areaId": "19",
    "PCSYCityID": "CN_440000_440300_0",
    "mt_xid": "V2_52007VwMUW11aUFgdTB1YBWQDEFtfX1RYHUgbbFVlBkFSCgpaDh1IGVlQNVYiUVxbVUYeTgVcA3YAElleW1lYGXkbbAdXMxVaWl9T",
    "unpl": "V2_ZzNsbRJVRkZ1XxRcLxtdBWJWQAheFi0SfQ9BVUsaXQZgHxNaXldFBHYITVd4El4DVwMiXkNVRRZ2C0JWfClda2ALFVpDZ3MVdzhHZHsfVQVlARBfR1NHFXYIRF15HloHZQIQbRJVRkZ1XxRcLxtdBWJWQAhyUEQUfA%3D%3D",
    "__jdv": "229668127|cn.bing.com|t_2037222536_0_0|adrealizable|a34b1fc9e3014dcd-p_0|1781702561985",
    "mba_muid": "17813333455121383673303",
    "wlfstk_smdl": "5ezxmt6fieitg0cm9w9hd5yb816jkluq",
    "thor": "7BD31B7110BD37A84B08A9D1B245E50CC89FE8BEFAE1AE9492CA9CAA5AAF0EA33D7DD55A8D72CF1F9F4645F67F1FE17978FFD82834CB800744174B9048227B5EE6F6341DFD0E09B1263264B401B6386C72F5D2D3BA96F56F0A98923987B266A4984B9D9AFFD61EEAD68D102C00AE7FC0C49BC884A028A1A2C3471F8E05DF34785F95B69FDDDFE7C5D4EABABACF34F54C52375D40D614D478F727FCA6BDDA5629",
    "light_key": "AASBKE7rOxgWQziEhC_QY6yahWpwFnpD2-lJFzcsH02D3TCSKrFjWIuUXXPDepU0J5EMgUto",
    "ceshi3.com": "000",
    "__jdc": "143920055",
    "cid": "9",
    "ipLoc-djd": "19-1607-4773-62123",
    "__jda": "143920055.17813333455121383673303.1781333345.1781706258.1781709349.6",
    "cn": "5",
    "flash": "3_RFwMproCWTBPEjc0AnZ2X0rld5Ur6GATrXPblfqD0lApwUlbtzMKyTxaybhUoGC_kjr-qUTyAaI6QAqZjdIFA5F0wBlam53PGj_7rkzjtv8Pc9WogxDqlDqG2OnGJGrJNigV4Cvnbrob1iufLFvlzwOygStHtcgQXf4mgjUVvdgowWdvHg_p",
    "__jdb": "143920055.8.17813333455121383673303|6.1781709349",
    "3AB9D23F7A4B3CSS": "jdd03EANAHMAEUEZWYF6H3GBD33BSZJHXIMJNGK6UMTVZCS4OUHGQZUDXP3FBWAN45GCUGCYCM2OHZ7BCPIJT2JGXIKFQ3YAAAAM62Y6MAWQAAAAACUZTZ7WY6WC6G4X",
    "_gia_d": "1",
    "shshshfpb": "BApXWsVc01ftA-XnMjhGyxozewqkKlQ_8BsNYNUhq9xJ1PdZfQofklRXYqj3UJZ9lVebi_Kvnsaxhcro97K9d7I0tNluxrc6rJkE",
    "3AB9D23F7A4B3C9B": "EANAHMAEUEZWYF6H3GBD33BSZJHXIMJNGK6UMTVZCS4OUHGQZUDXP3FBWAN45GCUGCYCM2OHZ7BCPIJT2JGXIKFQ3Y",
    "sdtoken": "AAbEsBpEIOVjqTAKCQtvQu17CO5MrqdqYinOdsDvZOhNOw7Qtl8hvu43sAKUv7n-s9V5KblHdnogCD5jK_AB1WKoaw46AWd6zG7dkdzD8gzVGBxietEQvOg3z76Mfc15fa6UYMv4wcn64jUrF_aLTEP-68a8qkNq2K-uSoN-CwWU"
}

# ============================================================
# Step 3: 发送请求 (使用 curl_cffi 模拟 Chrome 130 TLS)
# ============================================================
print("\n[3] 请求搜索 API (Chrome 130 TLS 指纹)...")

resp = requests.get(
    "https://api.m.jd.com/api",
    params=params,
    headers=headers,
    cookies=cookies,
    timeout=15,
    impersonate="chrome124",  # ★ 模拟 Chrome TLS 指纹 (绕过 JD CDN 的 TLS 检测)
)

print(f"[3] HTTP Status: {resp.status_code}")
print(f"[3] Response ({len(resp.text)} bytes)")

try:
    resp_json = resp.json()
    code = resp_json.get("code", "N/A")
    print(f"[3] API code: {code}")
    print(resp_json)

    if code == "0" or code == 0:
        print("\n" + "=" * 60)
        print("  [SUCCESS] 补环境验证通过! API 返回正常数据!")
        print("=" * 60)
        data_obj = resp_json.get("data", [])
        if isinstance(data_obj, list) and len(data_obj) > 0:
            print(f"\n  搜索结果数: {len(data_obj)}")
            first = data_obj[0]
            print(f"  第一条商品预览:")
            print(f"  {json.dumps(first, ensure_ascii=False)[:400]}")
    elif code == "403":
        print("\n[FAIL] API 返回 403: 签名/认证失败")
        print(f"   {resp.text[:300]}")
    elif code == "605":
        print("\n[WARN] 触发风控验证 (code=605)")
        print("   => h5st 签名格式正确，通过基础签名校验")
        print("   => 但环境指纹触发了人机验证 (需更真实的浏览器数据)")
        disposal = resp_json.get("disposal", {})
        ev_content = disposal.get("evContent", "")
        try:
            ev = json.loads(ev_content)
            print(f"   => 验证类型: {ev.get('evTypeTip', 'N/A')}")
            print(f"   => 验证标题: {ev.get('title', 'N/A')}")
        except:
            pass
        print("   => 下一步: 提高指纹真实性 + 从服务端获取有效 token")
    else:
        print(f"\n[WARN] API 返回 code={code}")
        print(f"   {json.dumps(resp_json, ensure_ascii=False)[:500]}")

except json.JSONDecodeError:
    print(f"[3] (非JSON, {len(resp.text)} bytes): {resp.text[:500]}")
except Exception as e:
    print(f"[3] Exception: {type(e).__name__}: {e}")
