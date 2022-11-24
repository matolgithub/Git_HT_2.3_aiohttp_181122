import asyncio
from aiohttp import ClientSession


# async def index_status():
#     async with ClientSession() as session:
#         async with session.get('http://127.0.0.1:7000/') as resp:
#             return await resp.json()
#
#
# async def get_advertisements():
#     async with ClientSession() as session:
#         async with session.get('http://127.0.0.1:7000/advertisements') as resp:
#             return await resp.json()
#
#
# async def get_advertisement():
#     async with ClientSession() as session:
#         async with session.get('http://127.0.0.1:7000/ads/1') as resp:
#             return await resp.json()


async def create_advertisement():
    async with ClientSession() as session:
        async with session.post('http://127.0.0.1:7000/ads/', json={
            "title": "title_3",
            "description": "description_3",
        }) as resp:
            return await resp.text()


# async def delete_advertisement():
#     async with ClientSession() as session:
#         async with session.delete('http://127.0.0.1:7000/ads/1') as resp:
#             return await resp.text()


async def main():
    # response = await index_status()
    # print(response)

    # response = await get_advertisements()
    # print(response)

    # response = await get_advertisement()
    # print(response)

    response = await create_advertisement()
    print(response)  # {"id": 1}, {"id": 2}, {"id": 2} - from requests.txt

    # response = await delete_advertisement()
    # print(response)


asyncio.run(main())
