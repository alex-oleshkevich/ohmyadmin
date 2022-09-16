import pathlib
import sqlalchemy as sa
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from starception import StarceptionMiddleware
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import HTTPConnection, Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from examples.admin.brands import BrandResource
from examples.admin.categories import CategoryResource
from examples.admin.countries import CountryResource
from examples.admin.currencies import CurrencyResource
from examples.admin.customers import CustomerResource
from examples.admin.orders import OrderResource
from examples.admin.products import ProductResource
from examples.admin.users import UserResource
from examples.models import User
from ohmyadmin.app import OhMyAdmin, UserMenu
from ohmyadmin.auth import BaseAuthPolicy, UserLike
from ohmyadmin.nav import MenuItem
from ohmyadmin.storage import LocalDirectoryStorage

metadata = sa.MetaData()
Base = declarative_base()


def index_view(request: Request) -> Response:
    url = request.url_for('ohmyadmin_welcome')
    return Response(f'<a href="{url}">admin</a>')


class AuthPolicy(BaseAuthPolicy):
    async def authenticate(self, conn: HTTPConnection, identity: str, password: str) -> UserLike | None:
        stmt = sa.select(User).where(User.email == identity)
        result = await conn.state.dbsession.scalars(stmt)
        if (user := result.one_or_none()) and pbkdf2_sha256.verify(password, user.password):
            return user
        return None

    async def load_user(self, conn: HTTPConnection, user_id: str) -> UserLike | None:
        stmt = sa.select(User).where(User.id == int(user_id))
        result = await conn.state.dbsession.scalars(stmt)
        return result.one_or_none()

    def get_user_menu(self, conn: HTTPConnection) -> UserMenu:
        if conn.user.is_authenticated:
            return UserMenu(
                user_name=str(conn.user),
                avatar=conn.user.avatar,
                menu=[
                    MenuItem.to_url(text='My profile', url='/profile', icon='user'),
                    MenuItem.to_url(text='Settings', url='/settings', icon='settings'),
                ],
            )
        return super().get_user_menu(conn)


this_dir = pathlib.Path(__file__).parent
uploads_dir = this_dir / 'uploads'
engine = create_async_engine('postgresql+asyncpg://root:postgres@localhost/ohmyadmin', future=True)

admin = OhMyAdmin(
    engine=engine,
    template_dir=this_dir / 'templates',
    file_storage=LocalDirectoryStorage(this_dir / 'uploads'),
    resources=[
        ProductResource(),
        CustomerResource(),
        OrderResource(),
        CategoryResource(),
        BrandResource(),
        CurrencyResource(),
        CountryResource(),
        UserResource(),
    ],
)

app = Starlette(
    debug=True,
    middleware=[
        Middleware(StarceptionMiddleware),
        Middleware(SessionMiddleware, secret_key='key!', path='/'),
    ],
    routes=[
        Route('/', index_view),
        Mount('/admin', admin),
    ],
)
