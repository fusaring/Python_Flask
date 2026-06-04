from playwright.sync_api import sync_playwright
import requests
from urllib.parse import quote
headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',   # 去掉 br
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        # 可选：添加以下两个字段（虽然 requests 不会自动发送，但加上无妨）
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
def get_qidian_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.qidian.com')
        # 等待页面加载完成
        page.wait_for_selector('body')
        cookies = page.context.cookies()
        browser.close()
        # 转换为 requests 可用的字典
        return {c['name']: c['value'] for c in cookies}

# 获取真实 cookies
cookies = get_qidian_cookies()
# print(cookies)
# 使用 requests.Session 并设置 cookies
session = requests.Session()
session.cookies.update(cookies)
session.headers.update(headers)
a = "凡人修仙传"
keyword=quote(a, encoding='utf-8')
page = 1
url = f'https://www.qidian.com/so/{keyword}.html?page={page}'
# 现在搜索应该成功
resp = session.get(url)
print(resp)
