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
