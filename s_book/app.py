import re
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, flash, abort
import pymysql
from urllib.parse import quote, urljoin

app = Flask(__name__)
app.secret_key = 'your-dev-123'

# 数据库配置（修改为你的）
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'myblog',
    'charset': 'utf8mb4'
}

# ---------- 笔趣阁配置 ----------
BQ_BASE_URL = "http://www.biquge.site"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

def get_db():
    return pymysql.connect(**DB_CONFIG)

# ---------- 数据库操作函数 ----------
def get_chapter_by_index(book_id, chapter_index):
    """根据书籍ID和章节序号查询缓存"""
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        "SELECT * FROM chapters WHERE book_id = %s AND chapter_index = %s",
        (book_id, chapter_index)
    )
    chapter = cursor.fetchone()
    cursor.close()
    conn.close()
    return chapter

def save_chapter(book_id, chapter_index, title, url, content):
    """保存章节内容到数据库"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chapters (book_id, chapter_index, title, url, content) VALUES (%s, %s, %s, %s, %s)",
        (book_id, chapter_index, title, url, content)
    )
    conn.commit()
    cursor.close()
    conn.close()

# ---------- 笔趣阁请求封装 ----------
def biquge_request(url):
    """发送请求，返回 BeautifulSoup 对象"""
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.encoding = 'utf-8'
    if resp.status_code != 200:
        print(f"请求失败: {url}, 状态码: {resp.status_code}")
        return None
    return BeautifulSoup(resp.text, 'lxml')

# ---------- 搜索 ----------
def search_biquge(keyword, page=1):
    """搜索书籍，返回书籍列表"""
    encoded_keyword = quote(keyword)
    url = f"{BQ_BASE_URL}/search/result.html?searchkey={encoded_keyword}"
    soup = biquge_request(url)
    if not soup:
        return []
    
    books = []
    items = soup.select('li')
    for item in items:
        name_elem = item.select_one('.novelname')
        if not name_elem:
            continue
        title = name_elem.get_text(strip=True)
        book_url = name_elem.get('href')
        if book_url and not book_url.startswith('http'):
            book_url = urljoin(BQ_BASE_URL, book_url)
        
        book_id = None
        if book_url:
            match = re.search(r'/(\d+)/?$', book_url) or re.search(r'/(\w+)/?$', book_url)
            if match:
                book_id = match.group(1)
        
        author_elem = item.select('span:nth-of-type(2) > a')
        author = author_elem[0].get_text(strip=True) if author_elem else '未知'
        
        cover_elem = item.select_one('img')
        cover = cover_elem.get('src') if cover_elem else ''
        if cover and not cover.startswith('http'):
            cover = urljoin(BQ_BASE_URL, cover)
        
        intro_elem = item.select_one('.intro')
        intro = intro_elem.get_text(strip=True) if intro_elem else ''
        
        last_elem = item.select_one('.last > a')
        last_chapter = last_elem.get_text(strip=True) if last_elem else ''
        
        books.append({
            'title': title,
            'author': author,
            'intro': intro[:200] + '...' if len(intro) > 200 else intro,
            'book_id': book_id,
            'cover': cover,
            'url': book_url,
            'last_chapter': last_chapter
        })
        if len(books) >= 20:
            break
    return books

# ---------- 书籍详情 ----------
def get_book_detail(book_id, book_url=None):
    if not book_url:
        book_url = f"{BQ_BASE_URL}/book/{book_id}/"
    soup = biquge_request(book_url)
    if not soup:
        return {}
    
    title_elem = soup.select_one('h1')
    title = title_elem.get_text(strip=True) if title_elem else '未知'
    
    author_elem = soup.select_one('.novelinfo-l li:nth-of-type(1) > a')
    author = author_elem.get_text(strip=True) if author_elem else '未知'
    
    cover_elem = soup.select_one('.novelinfo-r > img')
    cover = cover_elem.get('src') if cover_elem else ''
    if cover and not cover.startswith('http'):
        cover = urljoin(BQ_BASE_URL, cover)
    
    intro_elems = soup.select('p')
    intro = ' '.join([p.get_text(strip=True) for p in intro_elems]) if intro_elems else ''
    
    kind_elem = soup.select_one('.novelinfo-l li:nth-of-type(2) > a')
    kind = kind_elem.get_text(strip=True) if kind_elem else ''
    
    last_elem = soup.select_one('.novelinfo-l li:nth-of-type(6) > a')
    last_chapter = last_elem.get_text(strip=True) if last_elem else ''
    
    toc_url = book_url
    if toc_url and not toc_url.startswith('http'):
        toc_url = urljoin(BQ_BASE_URL, toc_url)
    
    return {
        'title': title,
        'author': author,
        'cover': cover,
        'intro': intro,
        'kind': kind,
        'last_chapter': last_chapter,
        'toc_url': toc_url
    }

# ---------- 目录 ----------
def get_catalog(toc_url):
    """获取目录列表，每个章节包含序号和URL"""
    soup = biquge_request(toc_url)
    if not soup:
        return []
    
    catalog = []
    chapters = soup.select('.dirlist > li')
    for idx, li in enumerate(chapters, start=1):
        a = li.select_one('a')
        if not a:
            continue
        title = a.get_text(strip=True)
        url = a.get('href')
        if url and not url.startswith('http'):
            url = urljoin(BQ_BASE_URL, url)
        catalog.append({
            'title': title,
            'url': url,
            'vip': False,
            'index': idx
        })
    return catalog

# ---------- 章节内容（抓取） ----------
def fetch_chapter_content(chapter_url):
    """从网络获取章节正文"""
    soup = biquge_request(chapter_url)
    if not soup:
        return {'title': '章节', 'content': '获取失败'}
    
    title_elem = soup.select_one('h1')
    title = title_elem.get_text(strip=True) if title_elem else '章节'
    
    content_elems = soup.select('p')
    content = '\n'.join([p.get_text(strip=True) for p in content_elems]) if content_elems else '正文获取失败'
    return {'title': title, 'content': content}

# ---------- 路由 ----------
@app.route('/')
def index():
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM books ORDER BY added_time DESC")
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index_book.html', books=books)

@app.route('/search')
def search():
    keyword = request.args.get('q', '').strip()
    books = []
    if keyword:
        books = search_biquge(keyword)
        print('获取到书籍数量:', len(books))
    return render_template('search.html', keyword=keyword, books=books)

@app.route('/add', methods=['POST'])
def add_book():
    book_id = request.form.get('book_id')
    if not book_id:
        flash('书籍ID缺失', 'danger')
        return redirect(url_for('book.search'))
    
    # book_url 可选，如果前端不传，内部会基于 book_id 构造
    book_url = request.form.get('url')  # 可以省略，get_book_detail 内部会处理
    detail = get_book_detail(book_id, book_url)
    if not detail:
        flash('获取书籍详情失败', 'danger')
        return redirect(url_for('book.search'))
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO books (qidian_id, title, author, cover_url, intro, last_chapter) VALUES (%s, %s, %s, %s, %s, %s)",
            (book_id, detail['title'], detail['author'], detail['cover'], detail['intro'], detail['last_chapter'])
        )
        conn.commit()
        flash(f'《{detail["title"]}》已添加到书架', 'success')
    except pymysql.err.IntegrityError:
        flash('这本书已经在书架中', 'warning')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:book_id>')
def delete_book(book_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('已从书架删除', 'info')
    return redirect(url_for('index'))

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    cursor.close()
    conn.close()
    if not book:
        flash('书籍不存在', 'danger')
        return redirect(url_for('index'))
    
    catalog_url = f"{BQ_BASE_URL}/book/{book['qidian_id']}/"
    catalog = get_catalog(catalog_url)
    return render_template('book.html', book=book, catalog=catalog)

@app.route('/read/<int:book_id>/<int:chapter_index>')
def read_chapter(book_id, chapter_index):
    # 1. 获取书籍信息
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    if not book:
        cursor.close()
        conn.close()
        abort(404)
    qidian_id = book['qidian_id']
    
    # 更新阅读进度（确保 books 表有 last_read_chapter_index 字段）
    cursor.execute(
        "UPDATE books SET last_read_chapter_index = %s WHERE id = %s",
        (chapter_index, book_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    # 2. 获取目录（用于导航和总章节数）
    catalog_url = f"{BQ_BASE_URL}/book/{qidian_id}/"
    catalog = get_catalog(catalog_url)  # 返回列表，每个元素包含 index, title, url
    total_chapters = len(catalog)
    
    # 3. 获取当前章节内容（缓存或抓取）
    cached = get_chapter_by_index(qidian_id, chapter_index)
    if cached:
        content = {
            'title': cached['title'],
            'content': cached['content']
        }
    else:
        # 从目录中找到当前章节的 URL
        target = next((item for item in catalog if item['index'] == chapter_index), None)
        if not target:
            abort(404)
        chapter_url = target['url']
        chapter_title = target['title']
        content_data = fetch_chapter_content(chapter_url)
        if not content_data or content_data['content'] == '获取失败':
            abort(500)
        save_chapter(qidian_id, chapter_index, chapter_title, chapter_url, content_data['content'])
        content = content_data
    
    # 4. 计算上一章、下一章的索引
    prev_index = chapter_index - 1 if chapter_index > 1 else None
    next_index = chapter_index + 1 if chapter_index < total_chapters else None
    
    return render_template('chapter.html',
                           content=content,
                           book_id=book_id,
                           current_index=chapter_index,
                           total_chapters=total_chapters,
                           prev_index=prev_index,
                           next_index=next_index,
                           book_title=book['title'])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)