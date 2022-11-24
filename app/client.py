import asyncio
from aiohttp import ClientSession


# successfully
async def index_status():
    async with ClientSession() as session:
        async with session.get('http://127.0.0.1:7000/') as resp:
            return await resp.json()


# succesfully
async def get_advertisement():
    async with ClientSession() as session:
        async with session.get('http://127.0.0.1:7000/ads/3') as resp:
            return await resp.json()


# successfully
async def create_advertisement():
    async with ClientSession() as session:
        async with session.post('http://127.0.0.1:7000/ads/', json={
            "title": "title_3",
            "description": "description_3",
        }) as resp:
            return await resp.text()


# successfully
async def patch_advertisement():
    async with ClientSession() as session:
        async with session.patch('http://127.0.0.1:7000/ads/3', json={
            "title": "Продам 2-этажный дом!",
            "description": "Корпич, 250м.кв.",
        }) as resp:
            return await resp.text()


# successfully
async def delete_advertisement():
    async with ClientSession() as session:
        async with session.delete('http://127.0.0.1:7000/ads/2') as resp:
            return await resp.text()


async def main():
    response = await index_status()

    print(response)
    # The result is: {'index_page': 'successfully'}

    response = await get_advertisement()
    print(response)
    # The result is:
    # {'id': 1, 'title': 'title_1', 'description': 'description_1', 'creation_date': 1669297866, 'user_id': None, 'owner': None}
    # {'id': 3, 'title': 'Продам дом', 'description': 'Самый красивый дом в районе.', 'creation_date': 1669298978, 'user_id': None, 'owner': None}
    # from requests.http: {
    # "id": 2,
    # "title": "title_2",
    # "description": "description_2",
    # "creation_date": 1669298582,
    # "user_id": null,
    # "owner": null
    # }

    response = await create_advertisement()
    print(response)
    # The result is: {"id": 1}, {"id": 2}, {"id": 2} - from requests.http

    response = await patch_advertisement()
    print(response)
    # The result: {"status": "success"}

    response = await delete_advertisement()
    print(response)
    # The result of delete id=2: {"status": "success"}


asyncio.run(main())
