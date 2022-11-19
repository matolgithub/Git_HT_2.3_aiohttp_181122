import datetime
import json
from typing import Type, Callable, Awaitable

from auth import hash_password, check_password

from aiohttp import web
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from config import PG_DSN, TOKEN_TTL
from models import Base, Advertisement, User, Token

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
