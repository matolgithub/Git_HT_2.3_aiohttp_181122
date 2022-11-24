from os import getenv
import json
from typing import Type, Callable, Awaitable

from aiohttp import web
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from dotenv import load_dotenv

from models import Base, Advertisement, User


load_dotenv()

PG_DSN = getenv("PG_DSN")
engine = create_async_engine(PG_DSN)

Session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

ERROR_TYPE = Type[web.HTTPForbidden] | Type[web.HTTPNotFound]


def raise_http_error(error_class: ERROR_TYPE, message: str | dict):
    raise error_class(
        text=json.dumps({"status": "error", "description": message}),
        content_type="application/json"
    )


async def get_orm_item(item_class: Type[Advertisement] | Type[User], item_id: int | str,
                       session: Session) -> Advertisement | User:
    item = await session.get(item_class, item_id)
    if item is None:
        raise raise_http_error(web.HTTPNotFound, f"{item_class.__name__} not found")

    return item


@web.middleware
async def session_middleware(
        request: web.Request, handler: Callable[[web.Request], Awaitable[web.Response]]
) -> web.Response:
    async with Session() as session:
        request["session"] = session
        return await handler(request)


class IndexView(web.View):
    async def get(self):
        return web.json_response({'index_page': 'successfully'})


class AdsView(web.View):

    async def get(self):
        advertisement_id = int(self.request.match_info["ads_id"])
        advertisement = await get_orm_item(Advertisement, advertisement_id, self.request["session"])

        return web.json_response(
            {"id": advertisement.id, "title": advertisement.title, "description": advertisement.description,
             "creation_date": int(advertisement.creation_date.timestamp()), "user_id": advertisement.user_id,
             "owner": advertisement.owner})

    async def post(self):
        ads_data = await self.request.json()
        new_ads = Advertisement(**ads_data)
        self.request["session"].add(new_ads)
        await self.request["session"].commit()

        return web.json_response({"id": new_ads.id})

    async def patch(self):
        ads_id = int(self.request.match_info["ads_id"])
        ads_data = await self.request.json()
        ads = await get_orm_item(Advertisement, ads_id, self.request["session"])
        for field, value in ads_data.items():
            setattr(ads, field, value)
            self.request["session"].add(ads)
            await self.request["session"].commit()

            return web.json_response({"status": "success"})

    async def delete(self):
        ads_id = int(self.request.match_info["ads_id"])
        del_ads = await get_orm_item(item_class=Advertisement, item_id=ads_id, session=self.request["session"])
        await self.request["session"].delete(del_ads)
        await self.request["session"].commit()

        return web.json_response({"status": "success"})


async def app_context(app: web.Application):
    print("--------------start process!--------------")
    async with engine.begin() as conn:
        async with Session() as session:
            await session.commit()
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    print("--------------finish process!--------------")


if __name__ == "__main__":
    app = web.Application(middlewares=[session_middleware])
    app.cleanup_ctx.append(app_context)
    app.add_routes(
        [
            web.get("/", IndexView),
            web.get("/ads/{ads_id:\d+}", AdsView),
            web.post("/ads/", AdsView),
            web.patch("/ads/{ads_id:\d+}", AdsView),
            web.delete("/ads/{ads_id:\d+}", AdsView)
        ]
    )
    web.run_app(app, host="127.0.0.1", port=7000)
