from playwright.sync_api import sync_playwright
import json

def save_qidian_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # 无头模式
        context = browser.new_context()
        page = context.new_page()
        page.goto('https://www.qidian.com')
        # 等待页面加载完成，可以根据需要增加等待时间或选择器
        page.wait_for_timeout(3000)  # 等待3秒，确保 cookies 生成
        cookies = context.cookies()
        browser.close()
        
        # 转换为字典格式
        cookies_dict = {c['name']: c['value'] for c in cookies}
        with open('qidian_cookies.json', 'w') as f:
            json.dump(cookies_dict, f)
        print("Cookies 已保存到 qidian_cookies.json")

if __name__ == '__main__':
    save_qidian_cookies()