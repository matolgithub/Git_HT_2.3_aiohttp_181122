from os import getenv
import datetime
import json
from typing import Type, Callable, Awaitable

from auth import hash_password, check_password

from aiohttp import web
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# from dotenv import load_dotenv
from models import Base, Advertisement, User, Token

# load_dotenv()

PG_DSN = getenv("PG_DSN")
TOKEN_TTL = getenv("TOKEN_TTL")

engine = create_async_engine(PG_DSN)

Session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

ERROR_TYPE = Type[web.HTTPUnauthorized] | Type[web.HTTPForbidden] | Type[web.HTTPNotFound]


def raise_http_error(error_class: ERROR_TYPE, message: str | dict):
    raise error_class(
        text=json.dumps({"status": "error", "description": message}),
        content_type="application/json"
    )


async def get_orm_item(item_class: Type[Advertisement] | Type[User] | Type[Token], item_id: int | str,
                       session: Session) -> Advertisement | User | Token:
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


@web.middleware
async def auth_middleware(
        request: web.Request, handler: Callable[[web.Request], Awaitable[web.Response]]
) -> web.Response:
    token_id = request.headers.get("token")
    if not token_id:
        raise_http_error(web.HTTPForbidden, "incorrect token!")
    try:
        token = await get_orm_item(Token, token_id, request["session"])
    except web.HTTPNotFound:
        token = None
    if not token:
        raise_http_error(web.HTTPForbidden, "incorrect token!")
    elif token.token_creation_time + datetime.timedelta(seconds=TOKEN_TTL) < datetime.datetime.now():
        raise_http_error(web.HTTPForbidden, "the token has expired!")
    request["token"] = token
    return await handler(request)


def check_owner(request: web.Request, user_id: int):
    if not request["token"]:
        raise_http_error(web.HTTPForbidden, "access denied!")
    elif request["token"].user.id != user_id:
        raise_http_error(web.HTTPForbidden, "access for owner only!")


async def login(request: web.Request):
    login_data = await request.json()
    query = select(User).where(User.name == login_data["name"])
    result = await request["session"].execute(query)
    user = result.scalar()
    if not user or not check_password(login_data["password"], user.password):
        raise_http_error(web.HTTPUnauthorized, "incorrect login or password")

    token = Token(user=user)
    request["session"].add(token)
    await request["session"].commit()

    return web.json_response({"token": str(token.id)})


class AdsView(web.View):
    async def get(self):
        advertisement_id = int(self.request.match_info["advertisement_id"])
        advertisement = await get_orm_item(Advertisement, advertisement_id, self.request["session"])
        return web.json_response(
            {"id": advertisement.id, "title": advertisement.title, "description": advertisement.description,
             "creation_date": int(advertisement.creation_date.timestamp()), "owner": advertisement.owner}
        )

    async def post(self):
        ads_data = await self.request.json()
        new_ads = Advertisement(**ads_data)
        self.request["session"].add(new_ads)
        await self.request["session"].commit()
        return web.json_response({"id": new_ads.id})

    async def patch(self):
        ads_id = int(self.request.match_info["ads_id"])
        user_id = int(self.request.match_info["user_id"])
        check_owner(self.request, user_id=user_id)
        ads_data = await self.request.json()
        ads = await get_orm_item(item_class=Advertisement, item_id=ads_id, session=self.request["session"])
        for field, value in ads_data.items():
            setattr(__obj=ads, __name=field, __value=value)
            self.request["sessiom"].add(ads)
            await self.request["session"].commit()

            return web.json_response({"status": "success"})

    async def delete(self):
        ads_id = int(self.request.match_info["ads_id"])
        user_id = int(self.request.match_info["user_id"])
        check_owner(request=self.request, user_id=user_id)
        del_ads = await get_orm_item(item_class=Advertisement, item_id=ads_id, session=self.request["session"])
        await self.request["session"].delete(del_ads)
        await self.request["session"].commit()
        return web.json_response({"status": "success"})


async def app_context(app: web.Application):
    print("--------------start process!--------------")
    async with engine.begin() as conn:
        async with Session() as session:
            # await session.execute("CREATE EXTENSION IF NOT EXISTS 'uuid-ossp'")
            await session.commit()
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    print("--------------finish process!--------------")


async def get_app():
    app = web.Application(middlewares=[session_middleware])
    app_auth_required = web.Application(middlewares=[session_middleware, auth_middleware])

    app.cleanup_ctx.append(app_context)
    app.add_routes(
        [
            web.get("/{ads_id:\d+}", AdsView),
            web.post("/advertisements/", AdsView)
        ]
    )
    app_auth_required.add_routes(
        [
            web.patch("/{ads_id:\d+}", AdsView),
            web.delete("/{ads_id:\d+}", AdsView)
        ]
    )

    app.add_subapp(prefix="/advertisements", subapp=app_auth_required)

    return app
