import typing
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.types import Message, Receive, Scope, Send

from ohmyadmin.contrib.sqlalchemy import DatabaseSessionMiddleware


async def receive() -> Message:  # pragma: no cover
    return {}


async def send(message: Message) -> None:  # pragma: no cover
    ...


async def test_middleware_attaches_session() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        pass

    engine = create_async_engine(url='postgresql+asyncpg://')
    async_session = async_sessionmaker(engine)

    app = DatabaseSessionMiddleware(app, async_session=async_session)
    scope: dict[str, typing.Any] = {}
    await app(scope, receive, send)
    assert scope['state']['dbsession']
