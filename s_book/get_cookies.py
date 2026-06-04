import json
from playwright.sync_api import sync_playwright
import os
def save_qidian_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.qidian.com')
        page.wait_for_timeout(3000)
        cookies = page.context.cookies()
        browser.close()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        COOKIE_FILE = os.path.join(BASE_DIR, 'qidian_cookies.json')
        cookies_dict = {c['name']: c['value'] for c in cookies}
        with open(COOKIE_FILE , 'w', encoding='utf-8') as f:
            json.dump(cookies_dict, f, ensure_ascii=False, indent=2)
        print("Cookies saved.")

if __name__ == '__main__':
    save_qidian_cookies()