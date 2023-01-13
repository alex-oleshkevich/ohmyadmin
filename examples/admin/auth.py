import sqlalchemy as sa
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from starlette.authentication import BaseUser
from starlette.requests import Request

from examples.config import async_session
from examples.models import User
from ohmyadmin.authentication import BaseAuthPolicy


class AuthPolicy(BaseAuthPolicy):
    async def authenticate(self, request: Request, identity: str, password: str) -> BaseUser | None:
        async with async_session() as session:
            stmt = sa.select(User).where(User.email == identity)
            result = await session.scalars(stmt)
            if (user := result.one_or_none()) and pbkdf2_sha256.verify(password, user.password):
                return user
            return None

    async def load_user(self, conn: Request, user_id: str) -> BaseUser | None:
        async with async_session() as session:
            stmt = sa.select(User).where(User.id == int(user_id))
            result = await session.scalars(stmt)
            return result.one_or_none()
