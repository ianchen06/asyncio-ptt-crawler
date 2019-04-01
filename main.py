import re
import asyncio
import datetime
import traceback
import re

import uvloop
import aiohttp
from bs4 import BeautifulSoup
from pytz import timezone

from storage import to_file, to_es
from config import *
from client import fetch
from util import gen_full_url

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

async def get_total_page(session):
    html = await fetch(session, f'{HOST}/bbs/{BOARD}/index.html')
    total_page = int(re.findall(f'href="/bbs/{BOARD}/index(\d+).html">&lsaquo; 上頁</a>', html)[0]) + 1
    # print(total_page)
    return total_page

def find_detail_links(html):
    urls = re.findall(f'/bbs/{BOARD}/M.+\.html', html)
    return urls

async def get_detail_page(session, url):
    full_url = gen_full_url(url)
    html = await fetch(session, full_url)
    url = '-'.join(url[1:].split('/'))
    return html

def extract_fields(html):
    """
    Content parser
    """
    html = html.replace(u'\u3000', ' ')
    try:
        data = {}
        soup = BeautifulSoup(html, 'lxml')
        meta_dict = {line.select('span')[0].text: line.select('span')[1].text for line in soup.find_all(class_=re.compile('.+metaline.*'))}
        # print(meta_dict)
        data['title'] = meta_dict.get('標題')
        data['author'] = meta_dict.get('作者')
        data['board'] = meta_dict.get('看板')
        data['published_at'] = meta_dict.get('時間')
        data['timestamp'] = int(timezone("Asia/Taipei").localize(datetime.datetime.strptime(meta_dict.get('時間'), "%a %b %d %H:%M:%S %Y")).timestamp())
        # print(data['timestamp'])
        [x.extract() for x in soup.select_one('#main-content').select('.article-metaline')]
        [x.extract() for x in soup.select_one('#main-content').select('.article-metaline-right')]
        data['content'] = soup.select_one('#main-content').text.strip()
        # print(data['title'])
        return data
    except Exception as e:
        print(e)
        print(meta_dict)
        print(soup.find('link', rel="canonical"))
        print(traceback.print_tb(e.__traceback__))
        return {}

async def get_page(session, pg):
    html = await fetch(session, f'{HOST}/bbs/{BOARD}/index{pg}.html')
    urls = find_detail_links(html)
    for url in urls:
        html = await get_detail_page(session, url)
        data = extract_fields(html)
        data['url'] = gen_full_url(url)
        # print(data['url'])
        # await to_file(url, data)

        es_data = data
        # es_data['_id'] = urllib.parse.quote(es_data['url'])
        await to_es(session, es_data)

async def main():
    async with aiohttp.ClientSession() as session:
        total_page = TOTAL_PAGE or await get_total_page(session)
        stop_page = (total_page - NO_PAGE) if NO_PAGE else 0
        from_page = total_page
        wg = []
        while True:
            # print("%s, %s"%(from_page, stop_page))
            if from_page <= stop_page:
                print("DONE")
                break
            to_page = from_page - PAGE
            print("from_page: %s, to_page: %s"%(from_page, to_page))
            for pg in range(from_page, to_page, -1):
                # print(pg)
                wg.append(get_page(session, pg))
            await asyncio.gather(*wg)
            from_page = to_page
            wg = []


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
