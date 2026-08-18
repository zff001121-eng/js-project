import requests
from lxml import etree
import subprocess
from functools import partial

from loguru import logger

# 处理execjs编码报错问题, 需在 import execjs之前
subprocess.Popen = partial(subprocess.Popen, encoding="utf-8")
import execjs


session = requests.session()
url = "https://www.fangdi.com.cn/new_house/new_house.html"
headers = {
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "sec-ch-ua": "\"Chromium\";v=\"130\", \"Microsoft Edge\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}


def get_one_html():
    response = session.get(url, headers=headers,verify=False)
    logger.info("返回第一次响应的cookie:{}".format(response.cookies.get_dict()))
    obj_html = etree.HTML(response.text)
    print(response.text)
    content_data = obj_html.xpath('//meta[2]/@content')[0]
    func_code = obj_html.xpath('//script[1]/text()')[0]
    return content_data, func_code


def second_request():
    content_data, func_code = get_one_html()
    with open('222.js', encoding='utf-8', errors='ignore') as f:

        js_code = f.read().replace('"content_code"', content_data).replace("'func_code'", func_code)
    cookie = execjs.compile(js_code).call('get_cookie')
    logger.info("JS cookie({}): {}...{}".format(len(cookie), cookie[:80], cookie[-150:]))
    print(cookie)
    # 解析JS cookie name=value
    js_name = cookie.split(';')[0].split('=')[0]
    js_value = cookie.split(';')[0].split('=')[-1]
    logger.info("JS cookie名: {}, 值: {}...".format(js_name, js_value))
    logger.info(len(js_value))

    # 尝试不同cookie组合
    test_cases = [
        # ("仅JS cookie (新session)", {js_name: js_value}, True),
        # ("仅JS cookie (复用session)", {js_name: js_value}, False),
        ("双cookie", {'UA1L1zGonajvO': dict(session.cookies.get_dict()).get('UA1L1zGonajvO', ''), js_name: js_value}, False),
    ]

    for label, cookies, new_session in test_cases:
        s = requests.session() if new_session else session
        resp = s.get(url, headers=headers, cookies=cookies)
        resp.encoding = 'utf-8'
        print(resp.text)
        logger.info("{} -> 状态码:{}".format(label, resp.status_code))
        if resp.status_code == 200:
            logger.info("成功! 长度: {}".format(len(resp.text)))
            return
        elif resp.status_code != 412 and resp.status_code != 400:
            logger.info("新状态码! 内容: {}".format(resp.text[:200]))


if __name__ == '__main__':
    second_request()
