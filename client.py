async def fetch(session, url):
    cnt = 0
    while cnt < 3:
        try:
            async with session.get(url, headers={"cookie": "over18=1"}) as response:
                return await response.text()
        except Exception as e:
            print(f"{e}, cnt: {cnt}")
            cnt += 1

