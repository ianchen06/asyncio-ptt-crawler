import json
import uuid

import aiofiles

from config import *

async def to_file(url, data):
    url = url[1:].replace('/', '-').strip()
    async with aiofiles.open('data/%s.json'%url, mode='w') as f:
        await f.write(json.dumps(data, ensure_ascii=False))

async def to_es(session, data):
    _id = uuid.uuid5(uuid.NAMESPACE_URL, data['url'])
    async with session.post(f"http://{ES_URL}/{ES_INDEX}/doc/{_id}", json=data) as response:
        resp = await response.text()
        # print(resp)
        return resp
