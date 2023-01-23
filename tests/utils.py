from starlette.authentication import AuthCredentials, AuthenticationBackend, BaseUser
from starlette.requests import HTTPConnection, Request

from examples.models import User
from ohmyadmin.authentication import BaseAuthPolicy


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
