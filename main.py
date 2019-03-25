import re
import asyncio
import json
import uuid

import uvloop
import aiohttp
import aiofiles
from bs4 import BeautifulSoup

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
HOST = 'https://www.ptt.cc'
BOARD = 'Gossiping'
PAGE = 10
NO_PAGE = PAGE
TOTAL_PAGE = ''
ES_URL = "10.30.0.121:9200"
ES_INDEX = "ptt"

async def to_file(url, data):
    url = url[1:].replace('/', '-').strip()
    async with aiofiles.open('data/%s.json'%url, mode='w') as f:
        await f.write(json.dumps(data, ensure_ascii=False))

async def fetch(session, url):
    cnt = 0
    while cnt < 3:
        try:
            async with session.get(url, headers={"cookie": "over18=1"}) as response:
                return await response.text()
        except Exception as e:
            print(f"{e}, cnt: {cnt}")
            cnt += 1

async def get_total_page(session):
    html = await fetch(session, f'{HOST}/bbs/{BOARD}/index.html')
    total_page = int(re.findall(f'href="/bbs/{BOARD}/index(\d+).html">&lsaquo; 上頁</a>', html)[0])
    print(total_page)
    return total_page

def find_detail_links(html):
    urls = re.findall(f'/bbs/{BOARD}/M.+\.html', html)
    return urls

def gen_full_url(url):
    return f"{HOST}{url}"

async def get_detail_page(session, url):
    full_url = gen_full_url(url)
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
        print("error")
        return {}

async def to_es(session, data):
    _id = uuid.uuid5(uuid.NAMESPACE_URL, data['url'])
    async with session.post(f"http://{ES_URL}/{ES_INDEX}/doc/{_id}", json=data) as response:
        resp = await response.text()
        # print(resp)
        return resp

async def get_page(session, pg):
    html = await fetch(session, f'{HOST}/bbs/{BOARD}/index{pg}.html')
    urls = find_detail_links(html)
    for url in urls:
        html = await get_detail_page(session, url)
        data = extract_fields(html)
        data['url'] = gen_full_url(url)
        print(data['url'])
        # await to_file(url, data)

        es_data = data
        # es_data['_id'] = urllib.parse.quote(es_data['url'])
        await to_es(session, es_data)

async def main():
    async with aiohttp.ClientSession() as session:
        total_page = TOTAL_PAGE or await get_total_page(session)
        stop_page = total_page - NO_PAGE if NO_PAGE else 0
        from_page = total_page + 1
        wg = []
        while from_page > stop_page:
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
