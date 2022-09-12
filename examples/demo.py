import pathlib
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from starception import StarceptionMiddleware
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from examples.admin.categories import CategoryResource
from examples.admin.customers import CustomerResource
from examples.admin.orders import OrderResource
from examples.admin.products import ProductResource
from examples.admin.users import UserResource
from ohmyadmin.app import OhMyAdmin, UserMenu
from ohmyadmin.nav import MenuGroup, MenuItem
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

    def build_main_menu(self, request: Request) -> list[MenuItem]:
        return [
            MenuGroup(
                'Resources',
                [
                    MenuItem.to_resource(ProductResource),
                    MenuItem.to_resource(CustomerResource),
                    MenuItem.to_resource(OrderResource),
                    MenuItem.to_resource(CategoryResource),
                    MenuItem.to_resource(UserResource),
                ],
            ),
        ]


this_dir = pathlib.Path(__file__).parent
engine = create_async_engine('postgresql+asyncpg://root:postgres@localhost/ohmyadmin', future=True)

app = Starlette(
    debug=True,
    middleware=[
        Middleware(StarceptionMiddleware),
        Middleware(SessionMiddleware, secret_key='key!', path='/'),
    ],
    routes=[
        Route('/', index_view),
        Mount(
            '/admin',
            Admin(
                file_storage=LocalDirectoryStorage(this_dir / 'uploads'),
                template_dirs=[this_dir / 'templates'],
                routes=[
                    Mount('/resources/products', ProductResource(engine)),
                    Mount('/resources/customers', CustomerResource(engine)),
                    Mount('/resources/orders', OrderResource(engine)),
                    Mount('/resources/categories', CategoryResource(engine)),
                    Mount('/resources/users', UserResource(engine)),
                ],
            ),
        ),
    ],
)
