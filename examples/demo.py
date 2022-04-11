import pathlib
import sqlalchemy as sa
import typing
from sqlalchemy.orm import declarative_base, relationship
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starsessions import SessionMiddleware

from ohmyadmin.admin import OhMyAdmin
from ohmyadmin.dashboards import Dashboard
from ohmyadmin.fields import Field
from ohmyadmin.flash_messages import FlashMiddleware
from ohmyadmin.menus import MenuItem, UserMenu
from ohmyadmin.metrics import StatMetric
from ohmyadmin.resources import Resource
from ohmyadmin.routing import route
from ohmyadmin.tools import Tool

Base = declarative_base()


# class User(Base):
#     __tablename__ = "users"
#     id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
#     first_name = sa.Column(sa.String(128))
#     last_name = sa.Column(sa.String(128))
#     email = sa.Column(sa.String(128), unique=True, index=True)
#     password = sa.Column(sa.String(128))
#     permissions = sa.Column(sa.JSON, default=list, server_default='[]')
#     created_at = sa.Column(
#         sa.DateTime(timezone=True),
#         nullable=False,
#         default=datetime.datetime.now,
#         server_default=sa.func.now(),
#     )
#
#     @property
#     def avatar(self):
#         email_hash = hashlib.md5(self.email.encode()).hexdigest()
#         return f"https://www.gravatar.com/avatar/{email_hash}?s=128&d=identicon"
#
#     def get_id(self) -> int:
#         return self.id
#
#     def get_hashed_password(self) -> str:
#         return self.password
#
#     def get_display_name(self) -> str:
#         return f"{self.first_name} {self.last_name}".strip() or self.email
#
#     def get_scopes(self) -> list[str]:
#         return self.permissions
#
#     __str__ = get_display_name


class Order(Base):
    __tablename__ = "orders"
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    name_be = sa.Column(sa.String(256), nullable=True, default='')
    name_ru = sa.Column(sa.String(256), nullable=True, default='')
    name_la = sa.Column(sa.String(256), unique=True)

    @property
    def name(self) -> str:
        if self.name_ru:
            return f'{self.name_la} ({self.name_ru})'
        return str(self.name_la)

    def __str__(self) -> str:
        return str(self.name_be)


class Family(Base):
    __tablename__ = "families"
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    name_be = sa.Column(sa.String(256), nullable=True, server_default='', default='')
    name_ru = sa.Column(sa.String(256), nullable=True, server_default='', default='')
    name_la = sa.Column(sa.String(256), nullable=False, unique=True)
    order_id = sa.Column(sa.ForeignKey("orders.id"), nullable=False)
    order = relationship(Order)

    @property
    def name(self) -> str:
        if self.name_ru:
            return f'{self.name_la} ({self.name_ru})'
        return str(self.name_la)

    def __str__(self) -> str:
        return str(self.name_be)


#
# class Genus(Base):
#     __tablename__ = "genea"
#     name_be = sa.Column(sa.String(256), nullable=True, server_default='', default='')
#     name_ru = sa.Column(sa.String(256), nullable=True, server_default='', default='')
#     name_la = sa.Column(sa.String(256), nullable=False, unique=True)
#     family_id = sa.Column(sa.ForeignKey("families.id"), nullable=False)
#     family = relationship(Family)
#
#     @property
#     def name(self) -> str:
#         if self.name_ru:
#             return f'{self.name_la} ({self.name_ru})'
#         return self.name_la
#
#     def __str__(self) -> str:
#         return self.name_be


def user_menu_config(request: Request, user_menu: UserMenu) -> None:
    user_menu.name = 'Alex Oleshkevich'
    user_menu.photo = (
        'https://images.unsplash.com/photo-1502685104226-ee32379fefbe?ixlib=rb-1.2.1'
        '&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=3&w=256&h=256&q=80'
    )
    user_menu.items.append(MenuItem('My profile', url='/'))


def index_view(request: Request) -> Response:
    url = request.url_for('welcome')
    return Response(f'<a href="{url}">admin</a>')


class FileManager(Tool):
    title = 'File Manager'
    icon = 'file'

    async def index_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'file_manager/index.html')

    @route('/create')
    async def create_file_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'file_manager/create_file.html')

    @route('/delete')
    async def delete_file_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'file_manager/delete_file.html')


class Backup(Tool):
    title = 'Back ups'
    icon = 'database-export'

    async def index_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'file_manager/index.html')


class Calendar(Tool):
    title = 'Calendar'
    icon = 'calendar'

    async def index_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'calendar.html')


class Photos(Tool):
    title = 'Photos'
    icon = 'photo'

    async def index_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'photos.html')


class NewUsersMetric(StatMetric):
    title = 'New users'

    async def compute(self, request: Request) -> typing.Any:
        return 42


class NewBirdsMetric(StatMetric):
    title = 'New birds'

    async def compute(self, request: Request) -> typing.Any:
        return 2


class ObservationTrendMetric(StatMetric):
    title = 'Observation Trend'
    columns = 6

    async def compute(self, request: Request) -> typing.Any:
        return 2


class OverviewDashboard(Dashboard):
    title = 'Overview'
    icon = 'dashboard'
    metrics = [NewUsersMetric, NewBirdsMetric, ObservationTrendMetric]


# class UserResource(Resource):
#     title = 'User'
#     icon = 'users'
#     entity_class = User


class OrdersResource(Resource):
    title = 'Order'
    icon = 'list'
    fields = [
        Field('name_ru', title='Name (rus)', searchable=True, sortable=True, link=True),
        Field('name_be', title='Name (bel)', searchable=True, sortable=True),
        Field(
            'name_la',
            title='Name (lat)',
            searchable=True,
            sortable=True,
            description='Latin specie name',
            placeholder='Enter specie name',
            input_mode='email',
            autocomplete='family-name',
        ),
    ]
    entity_class = Order
    order_by = [Order.name_ru]


class FamiliesResource(Resource):
    title = 'Family'
    icon = 'list'
    fields = [
        Field('name_ru', title='Name (rus)', searchable=True, sortable=True),
        Field('name_be', title='Name (bel)', searchable=True, sortable=True),
        Field('name_la', title='Name (lat)', searchable=True, sortable=True),
        Field('order', title='Order', searchable=True, sortable=True, source='order.name_ru'),
    ]
    entity_class = Family
    query_joins = [Order]
    query_select_related = [Family.order]
    order_by = [Family.name_ru]


# class GenusResource(Resource):
#     title = 'Genera'
#     icon = 'feather'
#     entity_class = Genus


# class SpeciesResource(Resource):
#     title = 'Specie'
#     icon = 'feather'


this_dir = pathlib.Path(__file__).parent
admin = OhMyAdmin(
    database_url='postgresql+asyncpg://postgres:postgres@localhost/haj',
    user_menu_config=user_menu_config,
    template_dirs=[this_dir / 'templates'],
    tools=[Backup, FileManager, Calendar, Photos],
    dashboards=[OverviewDashboard],
    resources=[OrdersResource, FamiliesResource],
)

app = Starlette(
    debug=True,
    routes=[
        Route('/', index_view),
        Mount('/admin', admin),
    ],
    middleware=[
        Middleware(SessionMiddleware, secret_key='key!', path='/'),
        Middleware(FlashMiddleware),
    ],
)
