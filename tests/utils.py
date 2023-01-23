import typing
from starlette.applications import Starlette
from starlette.authentication import AuthCredentials, AuthenticationBackend, BaseUser
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import HTTPConnection, Request
from starlette.routing import Mount

from examples.models import User
from ohmyadmin.app import OhMyAdmin
from ohmyadmin.authentication import BaseAuthPolicy
from ohmyadmin.pages.base import BasePage


class SimpleBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials, BaseUser] | None:
        user = await conn.state.admin.auth_policy.load_user(conn, 1)
        return AuthCredentials([]), user


class AuthTestPolicy(BaseAuthPolicy):
    async def authenticate(self, request: Request, identity: str, password: str) -> BaseUser | None:
        return User(id='1')

    async def load_user(self, conn: HTTPConnection, user_id: str) -> BaseUser | None:
        return User(id='1')

    def get_authentication_backend(self) -> AuthenticationBackend:
        return SimpleBackend()


def create_test_app(pages: typing.Sequence[BasePage]) -> Starlette:
    return Starlette(
        routes=[Mount('/admin', OhMyAdmin(pages=pages, auth_policy=AuthTestPolicy()))],
        middleware=[
            Middleware(SessionMiddleware, secret_key='key!'),
        ],
    )
