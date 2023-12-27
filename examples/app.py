import pathlib

import sqlalchemy as sa
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starception import install_error_handler
from starlette.applications import Starlette
from starlette.authentication import BaseUser
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import HTTPConnection, Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import ASGIApp, Receive, Scope, Send

from examples import settings
from examples.models import User
from examples.resources.countries.resource import CountriesResource
from examples.resources.custom_form_layout import CustomProductFormView
from examples.resources.display_view import ProductView
from examples.resources.form_view import ProductFormView
from examples.resources.users_table import UsersTable
from ohmyadmin.app import OhMyAdmin
from ohmyadmin.authentication.policy import AuthPolicy
from ohmyadmin.storages.storage import FileSystemStorage
from ohmyadmin.theme import Theme

install_error_handler()

this_dir = pathlib.Path(__file__).parent

engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


def index_view(request: Request) -> Response:
    url = request.url_for("ohmyadmin.welcome")
    return Response(f'<a href="{url}">admin</a>')


class DatabaseSessionMiddleware:
    def __init__(self, app: ASGIApp, sessionmaker: async_sessionmaker) -> None:
        self.app = app
        self.sessionmaker = sessionmaker

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async with self.sessionmaker() as dbsession:
            scope.setdefault("state", {})
            scope["state"]["dbsession"] = dbsession
            await self.app(scope, receive, send)


class UserPolicy(AuthPolicy):
    async def authenticate(self, request: Request, identity: str, password: str) -> BaseUser | None:
        async with async_session() as session:
            stmt = sa.select(User).where(User.email == identity)
            result = await session.scalars(stmt)
            if (user := result.one_or_none()) and pbkdf2_sha256.verify(password, user.password):
                return user
            return None

    async def load_user(self, conn: HTTPConnection, user_id: str) -> BaseUser | None:
        async with async_session() as session:
            stmt = sa.select(User).where(User.id == int(user_id))
            result = await session.scalars(stmt)
            return result.one_or_none()


admin = OhMyAdmin(
    auth_policy=UserPolicy(),
    file_storage=FileSystemStorage(
        directory=this_dir / "media",
        url_prefix="/",
    ),
    theme=Theme(
        logo="https://jelpy.io/static/logo.svg",
        title="Jelpy",
    ),
    views=[
        UsersTable(),
        ProductView(),
        ProductFormView(),
        CustomProductFormView(),
        CountriesResource(),
    ],
)

app = Starlette(
    debug=True,
    middleware=[
        Middleware(DatabaseSessionMiddleware, sessionmaker=async_session),
        Middleware(SessionMiddleware, secret_key="key!", path="/"),
    ],
    routes=[
        Route("/", index_view),
        Mount("/admin", admin),
    ],
)
