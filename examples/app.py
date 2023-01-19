from starception import install_error_handler
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from examples import config
from examples.admin.auth import AuthPolicy
from examples.admin.products import ProductPage
from examples.admin.profile import ProfilePage
from examples.admin.settings import SettingsPage
from examples.admin.users import UserPage
from examples.config import async_session, file_storage
from ohmyadmin import menu
from ohmyadmin.app import OhMyAdmin
from ohmyadmin.contrib.sqlalchemy import DatabaseSessionMiddleware
from ohmyadmin.helpers import LazyURL
from ohmyadmin.resources import Resource, TableView


def index_view(request: Request) -> Response:
    url = request.url_for('ohmyadmin.welcome')
    return Response(f'<a href="{url}">admin</a>')


class UsersResource(Resource):
    icon = 'users'
    index_view_class = TableView


admin = OhMyAdmin(
    title='Admin Demo',
    logo_url='https://haj.aliashkevich.com/static/logo.svg',
    auth_policy=AuthPolicy(),
    template_dir=config.this_dir / 'templates',
    file_storage=file_storage,
    user_menu=[
        menu.MenuLink('My profile', '/admin/profile', icon='address-book'),
        menu.MenuLink('Settings', url=LazyURL(SettingsPage.get_path_name()), icon='address-book'),
    ],
    pages=[
        UsersResource(),
        UserPage(),
        ProductPage(),
        SettingsPage(),
        ProfilePage(),
    ],
)

install_error_handler()
app = Starlette(
    debug=True,
    middleware=[
        Middleware(DatabaseSessionMiddleware, async_session=async_session),
        Middleware(SessionMiddleware, secret_key='key!', path='/'),
    ],
    routes=[
        Route('/', index_view),
        Mount('/admin', admin),
    ],
)
