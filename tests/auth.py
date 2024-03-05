from starlette.authentication import BaseUser
from starlette.requests import HTTPConnection, Request

from ohmyadmin.authentication.policy import AuthPolicy
from tests.models import User


class AuthTestPolicy(AuthPolicy):
    def __init__(self, user: User) -> None:
        self.user = user

    async def authenticate(self, request: Request, identity: str, password: str) -> BaseUser | None:
        return self.user

    async def load_user(self, conn: HTTPConnection, user_id: str) -> BaseUser | None:
        return self.user
