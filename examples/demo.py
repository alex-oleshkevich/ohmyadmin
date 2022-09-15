import pathlib
import sqlalchemy as sa
import typing
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from starception import StarceptionMiddleware
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from examples.admin.brands import BrandResource
from examples.admin.categories import CategoryResource
from examples.admin.countries import CountryResource
from examples.admin.currencies import CurrencyResource
from examples.admin.customers import CustomerResource
from examples.admin.orders import OrderResource
from examples.admin.products import ProductResource
from examples.admin.users import UserResource
from ohmyadmin.app import OhMyAdmin, UserMenu
from ohmyadmin.nav import MenuItem
from ohmyadmin.storage import LocalDirectoryStorage

metadata = sa.MetaData()
Base = declarative_base()


def index_view(request: Request) -> Response:
    url = request.url_for('welcome')
    return Response(f'<a href="{url}">admin</a>')


class Admin(OhMyAdmin):
    def build_user_menu(self, request: Request) -> UserMenu:
        return UserMenu(
            user_name='Alex Oleshkevich',
            avatar='https://m.media-amazon.com/images/M/MV5BMTY2ODQ3NjMyMl5BMl5BanBnXkFtZTcwODg0MTUzNA@@._V1_.jpg',
            menu=[
                MenuItem.to_url(text='My profile', url='/profile', icon='user'),
                MenuItem.to_url(text='Settings', url='/settings', icon='settings'),
            ],
        )


class AuthPolicy:
    async def load_user(self, identity: str, password: str) -> typing.Any:
        ...

    def login(self, request: Request, user: typing.Any) -> None:
        ...

    def logout(self, request: Request, user: typing.Any) -> None:
        ...

    def get_user_menu(self, request: Request) -> UserMenu:
        ...


this_dir = pathlib.Path(__file__).parent
uploads_dir = this_dir / 'uploads'
engine = create_async_engine('postgresql+asyncpg://root:postgres@localhost/ohmyadmin', future=True)

admin = Admin(
    template_dir=this_dir / 'templates',
    file_storage=LocalDirectoryStorage(this_dir / 'uploads'),
    resources=[
        ProductResource(engine),
        CustomerResource(engine),
        OrderResource(engine),
        CategoryResource(engine),
        BrandResource(engine),
        UserResource(engine),
        CurrencyResource(engine),
        CountryResource(engine),
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
        Mount('/media', StaticFiles(directory=uploads_dir)),
        Mount('/admin', admin),
    ],
)
