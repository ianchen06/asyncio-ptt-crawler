import re
import asyncio
import json

import uvloop
import aiohttp
import aiofiles
from bs4 import BeautifulSoup

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
HOST = 'https://www.ptt.cc'
BOARD = 'stationery'
PAGE = 10

async def to_file(url, data):
    url = url[1:].replace('/', '-').strip()
    async with aiofiles.open('data/%s.json'%url, mode='w') as f:
        await f.write(json.dumps(data, ensure_ascii=False))

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def get_total_page(session):
    html = await fetch(session, f'{HOST}/bbs/{BOARD}/index.html')
    total_page = int(re.findall('href="/bbs/stationery/index(\d+).html">&lsaquo; 上頁</a>', html)[0])
    print(total_page)
    return total_page

def find_detail_links(html):
    urls = re.findall('/bbs/stationery/M.+\.html', html)
    return urls

async def get_detail_page(session, url):
    full_url = f"{HOST}{url}"
    html = await fetch(session, full_url)
    url = '-'.join(url[1:].split('/'))
    return html

def extract_fields(html):
    try:
        data = {}
        soup = BeautifulSoup(html, 'lxml')
        meta_vals = [x.text for x in soup.select('.article-meta-value')]
        data['author'] = meta_vals[0]
        data['board'] = meta_vals[1]
        data['title'] = meta_vals[2]
        data['published_at'] = meta_vals[3] 
        [x.extract() for x in soup.select_one('#main-content').select('.article-metaline')]
        [x.extract() for x in soup.select_one('#main-content').select('.article-metaline-right')]
        data['content'] = soup.select_one('#main-content').text.strip()
        # print(data['title'])
        return data
    except:
        return {}

async def get_page(session, pg):
    html = await fetch(session, f'{HOST}/bbs/{BOARD}/index{pg}.html')
    urls = find_detail_links(html)
    for url in urls:
        html = await get_detail_page(session, url)
        data = extract_fields(html)
        await to_file(url, data)

async def main():
    async with aiohttp.ClientSession() as session:
        total_page = await get_total_page(session)
        from_page = total_page
        wg = []
        while from_page > total_page - PAGE:
            to_page = from_page - PAGE
            print("from_page: %s, to_page: %s"%(from_page, to_page))
            for pg in range(from_page, to_page, -1):
                print(pg)
                wg.append(get_page(session, pg))
            await asyncio.gather(*wg)
            from_page = to_page
            wg = []


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
