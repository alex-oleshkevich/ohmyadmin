from starlette.authentication import BaseUser
from starlette.requests import HTTPConnection, Request

from ohmyadmin.authentication import AuthPolicy
from tests.models import User


class AuthTestPolicy(AuthPolicy):
    def __init__(self, user: User) -> None:
        self.user = user

    async def authenticate(self, request: Request, identity: str, password: str) -> BaseUser | None:
        if self.user.email == identity and self.user.password == password:
            return self.user
        return None

    async def load_user(self, conn: HTTPConnection, user_id: str) -> BaseUser | None:
        if str(self.user.id) == str(user_id):
            return self.user
        return None
