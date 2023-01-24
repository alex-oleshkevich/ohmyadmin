from starception import install_error_handler
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from examples import config
from examples.admin.actions_demo import Actions
from examples.admin.auth import AuthPolicy
from examples.admin.brands import Brands
from examples.admin.categories import Categories
from examples.admin.components import Components
from examples.admin.countries import Countries
from examples.admin.currencies import Currencies
from examples.admin.customers import Customers
from examples.admin.form_layouts.card_layout import CardLayout
from examples.admin.form_layouts.fieldset_layout import FieldSetLayout
from examples.admin.form_layouts.simple_layout import SimpleLayout
from examples.admin.form_layouts.stacked_layout import StackedLayout
from examples.admin.orders import Orders
from examples.admin.pages_demo.blank_page import BlankPage
from examples.admin.pages_demo.table_page import ProductsPage
from examples.admin.products import Products
from examples.admin.profile import ProfilePage
from examples.admin.settings import SettingsPage
from examples.admin.users import Users
from examples.config import async_session, file_storage
from ohmyadmin import menu
from ohmyadmin.app import OhMyAdmin
from ohmyadmin.contrib.sqlalchemy import DatabaseSessionMiddleware
from ohmyadmin.helpers import LazyURL


def index_view(request: Request) -> Response:
    url = request.url_for('ohmyadmin.welcome')
    return Response(f'<a href="{url}">admin</a>')


admin = OhMyAdmin(
    title='Admin Demo',
    # logo_url='https://haj.aliashkevich.com/static/logo_square.svg',
    auth_policy=AuthPolicy(),
    template_dir=config.this_dir / 'templates',
    file_storage=file_storage,
    user_menu=[
        menu.MenuLink('My profile', '/admin/profile', icon='address-book'),
        menu.MenuLink('Settings', url=LazyURL(SettingsPage.get_path_name()), icon='address-book'),
    ],
    pages=[
        Categories(),
        Brands(),
        Customers(),
        Orders(),
        Countries(),
        Currencies(),
        Users(),
        Products(),
        SettingsPage(),
        ProfilePage(),
        Actions(),
        Components(),
        CardLayout(),
        FieldSetLayout(),
        SimpleLayout(),
        StackedLayout(),
        ProductsPage(),
        BlankPage(),
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
