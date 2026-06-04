# 个人笔记：Flask 开发与小说爬虫项目全记录

> 本笔记用于个人学习，记录从 Flask 基础到反爬对抗的完整过程，不涉及商业用途。

## 一、Flask 获取前端输入框数据

### 1.1 表单数据 (Form Data)

- 前端：`<input name="username">`，表单 `method="POST"`
- 后端：`username = request.form.get('username')`

### 1.2 URL 查询参数 (GET)

- 前端：`<form method="GET">` 或直接 `?q=关键词`
- 后端：`keyword = request.args.get('q', '').strip()`
  - 注意：`.get('q')` 获取的是**值**（如“剑来”），不是 `q=剑来` 字符串。

### 1.3 JSON 数据 (AJAX)

- 前端：`fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({key:value})})`
- 后端：`data = request.get_json(); value = data.get('key')`

### 1.4 文件上传

- 前端：`<input type="file" name="file">`，表单需 `enctype="multipart/form-data"`
- 后端：`f = request.files.get('file')`

### 1.5 安全实践

- 使用 `.get(key, default)` 避免 KeyError
- 校验用户输入，防止 SQL 注入
- 类型转换：`int(request.args.get('page', 1))`
- 复杂表单推荐 Flask-WTF

---

## 二、HTTP 状态码 202 Accepted

### 含义

- 服务器已接受请求，但尚未处理完成（常用于异步任务）
- 在爬虫场景中，202 常表示**反爬验证**（需要先访问首页获取 Cookie）

### 如何获取最终数据？

1. **轮询**：服务器返回 `task_id` 或 `task_status_url`，客户端定期 GET 该 URL
2. **回调**：客户端提供 `callback_url`，服务器处理完成后主动 POST 结果

### 注意

- 202 本身不包含业务数据，需要二次请求
- 如果请求是同步的，应使用 200

---

## 三、URL 编码（中文转 %xx 格式）

### Python 实现

```python
from urllib.parse import quote
keyword = "凡人修仙传"
encoded = quote(keyword, encoding='utf-8')
print(encoded)  # 输出: %E5%89%91%E6%9D%A5
```

## 用于构建 URL

```python
url = f"https://www.abc.com/so/{encoded}.html?page={page}"
```

## 四、请求头（Headers）与 Session 管理

### 4.1 编码错误 `'latin-1' codec can't encode character`

- **原因**：headers 字典中包含了中文或非 ASCII 字符

- **解决**： 移除所有非 ASCII 字符，调试代码：
  
  ```python
  for k, v in headers.items():
   try:
       v.encode('latin-1')
   except UnicodeEncodeError:
       print(f"非法头部: {k} = {v}")
  ```
  
  ### 4.2 动态 Referer

- 不能全局固定，每次请求前根据关键词动态生成
  
  ```python
  def get_referer(keyword, page=1):
      return f'https://www.abc.com/so/{keyword}.html?page={page}'
  headers['Referer'] = get_referer(keyword, page)
  ```
  
  ### 4.3 Cookie 类型错误 'set' object is not subscriptable

- **原因**：传递给 cookies= 的值是集合 {'a', 'b'} 而非字典 {'a':'b'}

- **解决**：使用字典；或改用 Session 自动管理

### 4.4 使用 requests.Session() 维持会话

```python
  session = requests.Session()
  session.headers.update(headers)
  session.get('https://www.example.com')   # 先访问首页获取动态 Cookie
  resp = session.get(search_url)          # 后续请求自动携带 Cookie
```

- Session 会自动保存服务器通过 Set-Cookie 返回的所有 Cookie。

## 五、反爬问题及解决方案

### 5.1 状态码 202（首页或搜索页）

**现象**：浏览器能访问，Python 请求返回 202
**原因**：

- IP 被临时限制

- TLS 指纹被识别（requests 库特征明显）

- 缺少动态 Cookie

解决方案（由简到难）：

1.等待 10-30 分钟，或更换 IP（VPN/代理）

2.使用 curl_cffi 模拟浏览器 TLS 指纹：

```python
    from curl_cffi import requests
    session = requests.Session(impersonate="chrome120")
```

3.使用 Playwright 启动真实浏览器

### 5.2 状态码 200 但返回“未找到相关小说”

**原因**：没有携带有效 Cookie，服务器返回默认提示页
**解决**：使用 Session 并先访问首页

### 5.3 Playwright 安装与使用

```python
pip install playwright
playwright install   # 下载 Chromium, Firefox, WebKit
```

示例：

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.example.com/so/剑来.html')
    html = page.content()
    browser.close()
```

## 六、数据库相关（PyMySQL + MySQL 8.0）

### 错误：`cryptography package is required for sha256_password`

- **原因**：MySQL 8.0+ 默认认证插件需要 `cryptography` 库

- **解决**：`pip install cryptography`

- 或修改 MySQL 用户认证方式为 `mysql_native_password`

### 表结构示例

```python
-- 书籍表
CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qidian_id VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100),
    cover_url TEXT,
    intro TEXT,
    last_chapter VARCHAR(200),
    last_read_chapter_index INT DEFAULT NULL,
    added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 章节缓存表
CREATE TABLE chapters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id VARCHAR(50) NOT NULL,
    chapter_index INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    url VARCHAR(500) NOT NULL,
    content LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_book_chapter (book_id, chapter_index)
);
```

## 七、Flask 应用接口设计（本项目）

| 路由                                        | 方法   | 功能         | 参数                         |
| ----------------------------------------- | ---- | ---------- | -------------------------- |
| `/`                                       | GET  | 首页，展示书架    | 无                          |
| `/search`                                 | GET  | 搜索书籍       | `?q=关键词`                   |
| `/add`                                    | POST | 添加书籍到书架    | `book_id`, `url`(可选)       |
| `/delete/<int:book_id>`                   | GET  | 删除书籍       | `book_id`                  |
| `/book/<int:book_id>`                     | GET  | 书籍详情 + 目录  | `book_id`                  |
| `/read/<int:book_id>/<int:chapter_index>` | GET  | 阅读章节（支持缓存） | `book_id`, `chapter_index` |

## 八、项目结构（最终）

```tex
myapp/
├── blueprints/
│   ├── __init__.py          # 导出 blueprints 列表
│   └── book.py              # 小说书架蓝图
├── templates/
│   ├── base.html            # 全局基础模板
│   └── book/                # 蓝图专用模板（可选）
│       ├── index_book.html
│       ├── search.html
│       ├── book.html
│       └── chapter.html
├── config.py                # 配置（含数据库）
├── requirements.txt
├── run.py                   # 启动入口
└── ... (其他原有文件)
```

## 九、蓝图（Blueprint）开发与常见问题

### 9.1 蓝图模板路径配置

- 问题：`render_template('index_book.html')` 报错 `TemplateNotFound`

- 原因：蓝图的 `template_folder` 是相对于蓝图文件所在目录，而非项目根目录

- 解决：
  
  - 将模板放到 `blueprints/templates/蓝图名/` 下；或
  
  - 删除 `template_folder` 参数，统一使用根目录的 `templates/` 文件夹

### 9.2 模板继承找不到 `base.html`

- 问题：子模板 `{% extends "base.html" %}` 报错

- 原因：`base.html` 放在了子目录（如 `templates/book/`）

- 解决：将 `base.html` 移至 `templates/` 根目录

### 9.3 蓝图中 `url_for` 报错 `BuildError`

- 问题：`url_for('index')` 提示 `Did you mean 'book.index'?`

- 原因：蓝图中端点自动加上蓝图名前缀（`book.`）

- 解决：
  
  - 使用 `url_for('book.index')`（完整名称）
  
  - 同一蓝图内使用 `url_for('.index')`（相对写法）

### 9.4 表单提交 404（蓝图前缀问题）

- 问题：`action="/add"` 提交后 404

- 原因：蓝图设置了 `url_prefix='/book'`，实际路由是 `/book/add`

- 解决：使用 `url_for` 动态生成：

```html
<form action="{{ url_for('book.add_book') }}" method="post">
```

### 9.5 蓝图中重定向

```python
return redirect(url_for('book.index'))   # 必须加蓝图名
```

## 十、前端响应式与样式优化

### 10.1 卡片图片比例控制

```html
<div class="col-4">
    <img src="..." style="width:100%; aspect-ratio:2/3; object-fit:cover;">
</div>
```

### 10.2 栅格列宽响应式

```html
<div class="col-6 col-md-4 col-lg-3">  <!-- 手机:2列，平板:3列，桌面:4列 -->
```

### 10.3 按钮组换行与间距

```html
<div class="d-flex flex-wrap gap-2">
    <a href="..." class="btn btn-sm btn-primary">阅读</a>
    <a href="..." class="btn btn-sm btn-outline-info">目录</a>
</div>
```

### 10.4 搜索框与按钮对齐（Bootstrap 输入组）

```html
<div class="input-group mb-4">
    <input type="text" name="q" class="form-control" placeholder="搜索...">
    <button class="btn btn-primary" type="submit">搜索</button>
</div>
```

### 10.5 移动端适配

- 在 `base.html` 中加入视口设置：

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
```

- 使用媒体查询调整字体和按钮大小

## 十一、章节缓存与“继续阅读”功能

### 11.1 章节缓存逻辑

- 阅读时先查 `chapters` 表，若有则直接返回

- 若无则从笔趣阁抓取，并保存到 `chapters` 表

### 11.2 记录最后阅读章节

- 在 `books` 表增加 `last_read_chapter_index` 字段

- 每次阅读时 `UPDATE books SET last_read_chapter_index = %s WHERE id = %s`

### 11.3 首页“继续阅读”按钮

```html
{% if book.last_read_chapter_index %}
    <a href="{{ url_for('book.read_chapter', book_id=book.id, chapter_index=book.last_read_chapter_index) }}" class="btn btn-sm btn-primary">📖 继续阅读</a>
{% else %}
    <a href="{{ url_for('book.read_chapter', book_id=book.id, chapter_index=1) }}" class="btn btn-sm btn-primary">📖 开始阅读</a>
{% endif %}
```

## 十二、笔趣阁爬虫规则集成（替代起点）

### 12.1 书源规则说明

- 搜索：`GET /search/result.html?searchkey={keyword}`

- 书籍列表选择器：`li`，书名 `.novelname`，作者 `span:nth-of-type(2) > a`

- 详情页：`h1` 书名，`.novelinfo-l li:nth-of-type(1) > a` 作者，`.novelinfo-r > img` 封面

- 目录：`.dirlist > li`，章节链接 `a@href`

- 章节内容：`p` 标签文本

### 12.2 BeautifulSoup 选择器兼容性

- **不支持 `nth-child`**，需改用 `nth-of-type`

- 示例：

```python
# 错误
author_elem = soup.select_one('.novelinfo-l li:nth-child(1) > a')
# 正确
author_elem = soup.select_one('.novelinfo-l li:nth-of-type(1) > a')
```

### 12.3 目录页与详情页同一 URL 的处理

- 直接将详情页 URL 作为目录 URL 传入 `get_catalog`，因为章节列表就在详情页中

---

## 十三、项目迁移与部署经验

### 13.1 从单文件 `app.py` 拆分为蓝图 + 工厂模式

- 将路由函数改为蓝图，并使用 `url_for('book.xxx')`

- 模板中的 `url_for` 也需加上蓝图名前缀

- 数据库配置移到 `config.py`，通过 `current_app.config` 读取

### 13.2 集成到已有 `myapp` 项目

- 创建 `blueprints/book.py`，定义 `book_bp`

- 在 `blueprints/__init__.py` 中导出 `blueprints = [book_bp]`

- 确保 `create_app` 中循环注册蓝图

- 合并模板文件，`base.html` 放在根 `templates` 目录

### 13.3 Docker 环境注意事项

- 依赖包需添加到 `requirements.txt`（`pymysql`, `requests`, `beautifulsoup4`, `lxml`）

- 若使用 Playwright，需在容器中安装系统依赖：`playwright install-deps`

- 数据库连接使用环境变量，避免硬编码

### 13.4 环境变量示例（`.env`）

```tex
DB_HOST=mysql
DB_USER=root
DB_PASSWORD=123456
DB_NAME=myblog
SECRET_KEY=your-secret-key
```

## 十四、常见错误与解决方案速查表

| 错误现象                                | 原因                            | 解决方案                                             |
| ----------------------------------- | ----------------------------- | ------------------------------------------------ |
| `TemplateNotFound`                  | 蓝图模板路径错误                      | 设置 `template_folder='../templates/book'` 或统一用根目录 |
| `BuildError: 'index'`               | 蓝图内未加前缀                       | 使用 `url_for('book.index')`                       |
| `NotImplementedError: nth-child`    | BeautifulSoup 不支持 `nth-child` | 改用 `nth-of-type` 或 `find_all`                    |
| `MissingSchema: None`               | 目录 URL 为 None                 | 检查 `get_book_detail` 中 `toc_url` 赋值              |
| 图片被压扁                               | `h-100` + `object-fit: cover` | 使用 `aspect-ratio` 固定比例                           |
| `pymysql.err.IntegrityError`        | 重复插入相同 `qidian_id`            | 添加唯一约束，捕获异常并提示“已存在”                              |
| `requests.exceptions.MissingSchema` | 请求 URL 为 None                 | 检查传入的 URL 变量是否为空                                 |

---

## 十五、调试技巧总结

1. 打印 `resp.status_code` 和 `resp.text[:500]` 查看实际返回内容

2. 使用浏览器开发者工具（F12 → Network）对比正常请求的 Headers 和 Cookie

3. 先写独立脚本测试爬虫，再集成到 Flask

4. 遇到 202 或反爬，先尝试 `curl_cffi`，再考虑 Playwright

5. 检查 headers 中是否有非法字符（非 ASCII）

6. 在 Flask 中开启调试模式：`app.run(debug=True)`，修改代码自动重载

---

## 十六、工具与资源推荐

### 16.1 `curl_cffi` 支持的 `impersonate` 参数

- Chrome: `chrome120`, `chrome124`, `chrome133a`, `chrome136`

- Safari: `safari17_0`, `safari18_0`, `safari_ios`

- Edge: `edge99`, `edge101`

- Firefox: `firefox133`

- 通用别名: `chrome`, `safari`, `edge`, `firefox`

### 16.2 Playwright 服务器部署依赖安装

```bash
playwright install-deps   # 自动安装 Chromium 所需的系统库
```

### 16.3 在线 CSS 选择器测试工具

- [SelectorGadget](https://selectorgadget.com/) – 点击页面元素自动生成选择器

- 浏览器控制台 `$$('selector')` 快速测试

### 16.4 其他实用库

- `browser-cookie3` – 读取浏览器本地 Cookie

- `python-dotenv` – 管理环境变量

- `gunicorn` – 生产 WSGI 服务器
