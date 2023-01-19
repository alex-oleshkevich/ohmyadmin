from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.types import ASGIApp, Receive, Scope, Send


class DatabaseSessionMiddleware:
    def __init__(self, app: ASGIApp, async_session: async_sessionmaker) -> None:
        self.app = app
        self.async_session = async_session

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with self.async_session() as session:
            scope.setdefault('state', {})
            scope['state']['dbsession'] = session
            await self.app(scope, receive, send)
