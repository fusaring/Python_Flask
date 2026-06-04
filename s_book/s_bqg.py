import requests
from urllib.parse import quote
import json


# 加载 cookies
def load_cookies():
    with open('qidian_cookies.json', 'r') as f:
        return json.load(f)

cookies = load_cookies()
session = requests.Session()

# 将从开发者工具中复制的请求头完整地放入字典中
a = "凡人修仙传"
keyword=quote(a, encoding='utf-8')
print(keyword)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.qidian.com/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'referer':f'https://www.qidian.com/so/{keyword}.html?page=1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
}
# cookies={
#     'e1':'%7B%22l6%22%3A%22%22%2C%22l7%22%3A%22%22%2C%22l1%22%3A3%2C%22l3%22%3A%22%22%2C%22pid%22%3A%22qd_P_Searchresult%22%2C%22eid%22%3A%22qd_S81%22%7D',
#     'e2':'%7B%22l6%22%3A%22%22%2C%22l7%22%3A%22%22%2C%22l1%22%3A3%2C%22l3%22%3A%22%22%2C%22pid%22%3A%22qd_P_Searchresult%22%2C%22eid%22%3A%22qd_S81%22%7D; newstatisticUUID=1775806293_2098424247', 
#     '_csrfToken':'oJuIJsspdDdjUnHtz0yPrCtgl2cUue12xC3gh4eK',
#     'traffic_utm_referer':'https%3A//yileila.top/', 
#     'fu':'493542954', 
#     'Hm_lvt_f00f67093ce2f38f215010b699629083':'1775806295', 
#     'HMACCOUNT':'DB49AB66B77C1EEB; supportwebp=true',
#     'Hm_lpvt_f00f67093ce2f38f215010b699629083':'1775828668', 
#     'w_tsfp':'ltvuV0MF2utBvS0Q7q/hlkOoETgnfDw4h0wpEaR0f5thQLErU5mC1I54ts3wMnDZ68xnvd7DsZoyJTLYCJI3dwNFQ5jDcN0UiQSQk9Vw1NoXCENlRM7fDQJNcLInujZBenhCNxS00jA8eIUd379yilkMsyN1zap3TO14fstJ019E6KDQmI5uDW3HlFWQRzaLbjcMcuqPr6g18L5a5TfY51nyK1MnUu5A1EPE1CEWXyom5kW5c7xfZk6qK5yuSqA='
# }


# 访问首页以获取初始Cookie

# 发送搜索请求

page = 1
url = f'https://www.qidian.com/so/{keyword}.html?page={page}'
print(url)
aa=session.get(url,cookies=cookies)
print(aa)
# response = session.get(url)

# if response.status_code == 200:
#     print("请求成功！",response.text)
#     # ... 你的解析逻辑
# else:
#     print(f"请求失败，状态码: {response.status_code}")