import pathlib
import sqlalchemy as sa
from async_storages import FileStorage, LocalStorage
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from starception import install_error_handler
from starlette.applications import Starlette
from starlette.authentication import BaseUser
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette_flash import flash

from examples.models import User
from ohmyadmin.app import OhMyAdmin
from ohmyadmin.authentication import BaseAuthPolicy, UserMenu
from ohmyadmin.datasource.sqla import SQLADataSource
from ohmyadmin.formatters import AvatarFormatter, BoolFormatter, DateFormatter
from ohmyadmin.pages.base import Page
from ohmyadmin.pages.table import TablePage
from ohmyadmin.resources import Resource, TableView
from ohmyadmin.shortcuts import get_admin
from ohmyadmin.views.table import TableColumn

metadata = sa.MetaData()
Base = declarative_base()
this_dir = pathlib.Path(__file__).parent
uploads_dir = this_dir / 'uploads'
engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost/ohmyadmin', future=True, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
file_storage = FileStorage(LocalStorage(this_dir / 'uploads'))


def index_view(request: Request) -> Response:
    url = request.url_for('ohmyadmin_welcome')
    return Response(f'<a href="{url}">admin</a>')


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

    def get_user_menu(self, request: Request) -> UserMenu:
        if request.user.is_authenticated:
            return UserMenu(
                user_name=str(request.user),
                avatar=get_admin(request).media_url(request, request.user.avatar),
                menu=[
                    # MenuLink(text='My profile', url=request.url_for(ProfilePage.url_name()), icon='user'),
                    # MenuLink(text='Settings', url=request.url_for(SettingsPage.url_name()), icon='settings'),
                ],
            )
        return super().get_user_menu(request)


class SettingsPage(Page):
    icon = 'settings'
    label_plural = 'Settings'
    template = 'settings_page.html'

    def post(self, request: Request) -> Response:
        flash(request).success('Operation successful.')
        return self.redirect_to_self(request)


class UserPage(TablePage):
    label = 'App users'
    datasource = SQLADataSource(User, async_session)
    columns = [
        TableColumn('photo', formatter=AvatarFormatter()),
        TableColumn('first_name'),
        TableColumn('last_name', searchable=True, sortable=True),
        TableColumn('email', searchable=True),
        TableColumn('is_active', sortable=True, formatter=BoolFormatter(as_text=True)),
        TableColumn('created_at', sortable=True, formatter=DateFormatter()),
    ]


class ProfilePage(Page):
    icon = 'user'


class UsersResource(Resource):
    icon = 'users'
    index_view_class = TableView


admin = OhMyAdmin(
    title='Admin Demo',
    logo_url='https://haj.aliashkevich.com/static/logo.svg',
    auth_policy=AuthPolicy(),
    template_dir=this_dir / 'templates',
    file_storage=file_storage,
    pages=[
        UsersResource(),
        UserPage(),
        SettingsPage(),
        ProfilePage(),
    ],
)

install_error_handler()
app = Starlette(
    debug=True,
    middleware=[
        Middleware(SessionMiddleware, secret_key='key!', path='/'),
    ],
    routes=[
        Route('/', index_view),
        Mount('/admin', admin),
    ],
)
