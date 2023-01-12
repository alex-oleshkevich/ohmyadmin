import pathlib
import sqlalchemy as sa
import typing
import wtforms
from async_storages import FileStorage, LocalStorage
from markupsafe import Markup
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

from examples.models import Product, User
from ohmyadmin import actions
from ohmyadmin.actions import ActionResponse, ModalAction
from ohmyadmin.app import OhMyAdmin
from ohmyadmin.authentication import BaseAuthPolicy, UserMenu
from ohmyadmin.datasource.sqla import SQLADataSource
from ohmyadmin.filters import (
    ChoiceFilter,
    DateFilter,
    DateRangeFilter,
    DecimalFilter,
    FloatFilter,
    IntegerFilter,
    MultiChoiceFilter,
    StringFilter,
)
from ohmyadmin.formatters import AvatarFormatter, BoolFormatter, DateFormatter, NumberFormatter
from ohmyadmin.pages.base import Page
from ohmyadmin.pages.table import TablePage
from ohmyadmin.resources import Resource, TableView
from ohmyadmin.shortcuts import get_admin
from ohmyadmin.views.table import TableColumn

metadata = sa.MetaData()
Base = declarative_base()
this_dir = pathlib.Path(__file__).parent
uploads_dir = this_dir / 'uploads'
engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost/ohmyadmin', future=True)
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
    filters = [
        StringFilter('first_name'),
        StringFilter('last_name'),
    ]


async def toggle_visibility(request: Request) -> Response:
    if request.method == 'GET':
        return Response(status_code=204)

    object_id = request.query_params.get('_ids')
    async with async_session() as session:
        await session.execute(sa.update(Product).where(Product.id == int(object_id)).values(visible=~Product.visible))
        await session.commit()
    return ActionResponse().show_toast('Visibility has been changed.').refresh_datatable()


async def delete_product_action(request: Request) -> Response:
    object_id = request.query_params.get('_ids')
    async with async_session() as session:
        product = await session.get(Product, int(object_id))
        await session.delete(product)
        await session.commit()
    return ActionResponse().show_toast('Product has been deleted.').refresh_datatable()


def product_name_validator(form, field):
    if field.data == 'fail':
        raise wtforms.ValidationError('Product name is invalid.')


class EditProductForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required(), product_name_validator])
    price = wtforms.DecimalField(validators=[wtforms.validators.data_required()])
    compare_at_price = wtforms.DecimalField(validators=[wtforms.validators.data_required()])
    sku = wtforms.IntegerField(default=0)
    quantity = wtforms.IntegerField(default=0)
    barcode = wtforms.StringField(default='')
    visible = wtforms.BooleanField(default=False)


class EditProductAction(ModalAction):
    title = 'Edit product'
    message: str = Markup('Feel free to update <b>{object.name}</b>.')
    form_class = EditProductForm

    async def dispatch(self, request: Request) -> Response:
        async with async_session() as session:
            request.state.db = session
            return await super().dispatch(request)

    async def get_object(self, request: Request) -> typing.Any | None:
        object_id = request.query_params.get('_ids')
        result = await request.state.db.scalars(sa.select(Product).where(Product.id == int(object_id)))
        return result.one()

    async def handle_submit(self, request: Request, form: wtforms.Form, instance: typing.Any | None) -> Response:
        form.populate_obj(instance)
        await request.state.db.commit()
        return ActionResponse().show_toast('Product has been updated.').refresh_datatable().close_modal()


class ProductPage(TablePage):
    label = 'Product'
    datasource = SQLADataSource(Product, async_session, sa.select(Product).order_by(Product.created_at.desc()))
    batch_actions = [
        actions.Modal('Edit info', EditProductAction(), 'pencil'),
    ]
    object_actions = [
        actions.Simple('Toggle visibility', toggle_visibility, 'eye', method='post'),
        actions.Modal('Edit info', EditProductAction(), 'pencil'),
        actions.Link('No icon', '#'),
        actions.Link('View profile', '#', 'eye'),
        actions.Simple(
            'Delete',
            delete_product_action,
            'trash',
            dangerous=True,
            method='delete',
            confirmation='Do you really want to delete this object?',
        ),
    ]
    columns = [
        TableColumn('name'),
        TableColumn('price', sortable=True, formatter=NumberFormatter(suffix='USD')),
        TableColumn('compare_at_price', sortable=True, formatter=NumberFormatter(suffix='USD')),
        TableColumn('sku', sortable=True, label='SKU'),
        TableColumn('quantity', sortable=True, label='Qty.'),
        TableColumn('barcode', searchable=True),
        TableColumn('visible', sortable=True, formatter=BoolFormatter(as_text=True)),
        TableColumn('availability', sortable=True, formatter=DateFormatter()),
        TableColumn('created_at', sortable=True, formatter=DateFormatter()),
    ]
    filters = [
        StringFilter('name'),
        DecimalFilter('price'),
        FloatFilter('compare_at_price'),
        IntegerFilter('sku'),
        DateFilter('created_at'),
        DateRangeFilter('created_at'),
        ChoiceFilter(
            'barcode',
            label='Bar code',
            choices=[
                ('0686594913423', 'Code 1'),
                ('0616403740810', 'Code 2'),
            ],
        ),
        MultiChoiceFilter(
            'quantity',
            choices=[
                (5, 'Five'),
                (15, 'Fifteen'),
            ],
            coerce=int,
        ),
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
        ProductPage(),
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
