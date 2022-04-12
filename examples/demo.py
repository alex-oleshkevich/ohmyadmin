import pathlib
import sqlalchemy as sa
import typing
import wtforms
from sqlalchemy import select
from sqlalchemy.orm import declarative_base, joinedload, relationship
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starsessions import SessionMiddleware

from ohmyadmin.admin import OhMyAdmin
from ohmyadmin.choices import TextChoices
from ohmyadmin.dashboards import Dashboard
from ohmyadmin.fields import CheckboxField, Field, IntegerSelectField, SelectField, TextareaField
from ohmyadmin.flash_messages import FlashMiddleware
from ohmyadmin.forms import Form
from ohmyadmin.menus import MenuItem, UserMenu
from ohmyadmin.metrics import StatMetric
from ohmyadmin.query import query
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


class RedBook(TextChoices):
    NO_RISK = 'no_risk'
    CATEGORY_I = 'category_1'
    CATEGORY_II = 'category_2'
    CATEGORY_III = 'category_3'
    CATEGORY_IV = 'category_4'


class IUCNRisk(TextChoices):
    EXTINCT = 'extinct'  # EX
    EXTINCT_IN_WILD = 'extinct_in_wild'  # EW
    CRITICALLY_ENDANGERED = 'critically_endangered'  # CR
    ENDANGERED = 'endangered'  # EN
    VULNERABLE = 'vulnerable'  # VU
    CONVERSATION_DEPENDENT = 'conversation_dependent'  # CD
    NEAR_THREATENED = 'near_threatened'  # NT
    LEAST_CONCERN = 'least_concern'  # LC
    DATA_DEFICIENT = 'data_deficient'  # DD
    NOT_EVALUATED = 'not_evaluated'  # NE


class Nesting(TextChoices):
    NOT_NESTING = 'not_nesting'
    NESTING = 'nesting'
    POSSIBLY_NESTING = 'possibly_nesting'


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


class Genus(Base):
    __tablename__ = "genea"
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    name_be = sa.Column(sa.String(256), nullable=True, server_default='', default='')
    name_ru = sa.Column(sa.String(256), nullable=True, server_default='', default='')
    name_la = sa.Column(sa.String(256), nullable=False, unique=True)
    family_id = sa.Column(sa.ForeignKey("families.id"), nullable=False)
    family = relationship(Family)

    @property
    def name(self) -> str:
        if self.name_ru:
            return f'{self.name_la} ({self.name_ru})'
        return self.name_la

    def __str__(self) -> str:
        return self.name_be


class Specie(Base):
    __tablename__ = "species"
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    name_be = sa.Column(sa.String(256), nullable=True, server_default='', default='')
    name_ru = sa.Column(sa.String(256), nullable=True, server_default='', default='')
    name_en = sa.Column(sa.String(256), nullable=True, server_default='', default='')
    name_la = sa.Column(sa.String(256), nullable=False, unique=True)

    description = sa.Column(sa.Text, nullable=False, default="", server_default="")  # внешний вид
    # appearance = sa.Column(sa.Text, nullable=False, default="", server_default="")  # внешний вид
    # distribution = sa.Column(sa.Text, nullable=False, default="", server_default="")  # распространение
    # voice = sa.Column(sa.Text, nullable=False, default="", server_default="")  # голос
    # biotope = sa.Column(sa.Text, nullable=False, default="", server_default="")  # место обитания
    # nutrition = sa.Column(sa.Text, nullable=False, default="", server_default="")
    # biology = sa.Column(sa.Text, nullable=False, default="", server_default="")
    # interesting_facts = sa.Column(sa.Text, nullable=False, default="", server_default="")
    # threat_factors = sa.Column(sa.Text, nullable=False, default="", server_default="")  # Основные факторы угрозы
    comment = sa.Column(sa.Text, nullable=False, default="", server_default="")
    sources = sa.Column(sa.Text, nullable=False, default="", server_default="")  # information sources

    migratory = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)  # Перелётный
    transiting = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)  # транзитно мигрирующий вид
    settled = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)  # Оседлый
    nesting = sa.Column(sa.String, nullable=False, default=False)
    """Гнездящийся, виды птиц, с доказанным в пределах области гнездованием."""
    nomadic = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)  # Кочующий
    wintering = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)
    """Зимующий, виды, не размножающиеся в пределах области, но регулярно встречающиеся в зимний период."""
    spanning = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)
    """пролётных, виды, появляющиеся в пределах региона во время миграций (пролета, кочевок)
    в негнездовой период или во время него."""
    straying = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)
    """залётная, виды, случайно оказавшиеся на территории области по каким-то причинам,
    пролетные пути и места гнездования которых находятся далеко за пределами области."""
    dimorphism = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)
    waterfowl = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)
    red_book = sa.Column(sa.String)
    iucn_risk = sa.Column(sa.String, nullable=False)
    genus_id = sa.Column(sa.ForeignKey("genea.id"), nullable=False)
    genus = relationship(Genus, cascade='save-update')

    # appearances = relationship('Appearance', cascade='all,delete-orphan')
    # photos = relationship('Photo', cascade='all,delete-orphan')
    # videos = relationship('Video', cascade='all,delete-orphan')
    # voices = relationship('Voice', cascade='all,delete-orphan')

    @property
    def name(self) -> str:
        if self.name_ru:
            return f'{self.name_ru} ({self.name_la})'
        return self.name_la

    def __str__(self) -> str:
        return self.name_be


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
            form_placeholder='Enter specie name',
            form_input_mode='email',
            form_autocomplete='family-name',
        ),
    ]
    entity_class = Order
    order_by = [Order.name_ru]


class FamiliesResource(Resource):
    title = 'Family'
    icon = 'list'
    fields = [
        Field('name_ru', title='Name (rus)', searchable=True, sortable=True, link=True),
        Field('name_be', title='Name (bel)', searchable=True, sortable=True),
        Field('name_la', title='Name (lat)', searchable=True, sortable=True),
        IntegerSelectField('order_id', title='Order', searchable=True, sortable=True, source='order.name_ru'),
    ]
    entity_class = Family
    queryset = select(Family).join(Order).order_by(Family.name_ru).options(joinedload(Family.order))

    async def choices_for_order_id(self, request: Request) -> list[tuple[str, typing.Any]]:
        stmt = select(Order).order_by(Order.name_la)
        return await query(request.state.db).choices(stmt)


class GeneraResource(Resource):
    title = 'Genus'
    title_plural = 'Genera'
    icon = 'feather'
    entity_class = Genus
    queryset = select(Genus).join(Family).order_by(Genus.name_ru).options(joinedload(Genus.family))
    fields = [
        Field('name_ru', title='Name (rus)', searchable=True, sortable=True, link=True, required=False),
        Field('name_be', title='Name (bel)', searchable=True, sortable=True, required=False),
        Field('name_la', title='Name (lat)', searchable=True, sortable=True),
        IntegerSelectField('family_id', title='Family', searchable=True, sortable=True, source='family.name_ru'),
    ]

    async def choices_for_family_id(self, request: Request) -> list[tuple[str, typing.Any]]:
        stmt = select(Family).order_by(Family.name_la)
        return await query(request.state.db).choices(stmt)


class SpeciesResource(Resource):
    title = 'Specie'
    icon = 'feather'
    entity_class = Specie
    queryset = (
        select(Specie, Genus)
        .join(Genus)
        .join(Family)
        .order_by(Specie.name_ru)
        .options(
            joinedload(Specie.genus),
            joinedload(Genus.family),
        )
    )
    fields = [
        Field('name_ru', title='Name (rus)', searchable=True, sortable=True, link=True, required=False),
        Field('name_be', title='Name (bel)', searchable=True, show_on=['form'], required=False, read_only=True),
        Field('name_la', title='Name (lat)', searchable=True, sortable=True, form_placeholder='Latin name.'),
        IntegerSelectField(
            'genus_id', title='Genus', searchable=True, sortable=True, source='genus.name_ru', show_on=['form']
        ),
        IntegerSelectField(
            'family_id',
            title='Family',
            searchable=True,
            sortable=True,
            source='genus.family.name_ru',
            show_on=['index'],
        ),
        TextareaField(
            'description',
            title='Description',
            show_on=['form'],
            read_only=True,
            description=(
                'Index: Appearance, Distribution, Voice, Biotope, Nutrition, Biology, Interesting facts, Threat factors'
            ),
            required=False,
        ),
        TextareaField(
            'comment',
            title='Comment',
            show_on=['form'],
            description='Additional comments (not visible to users).',
            required=False,
        ),
        TextareaField(
            'sources',
            title='Source',
            show_on=['form'],
            description='Used informational sources.',
            required=False,
        ),
        CheckboxField('migratory', title='Migratory', required=False, default_value=True),
        CheckboxField('transiting', title='Transit during migration', show_on=['form'], required=False),
        CheckboxField('settled', title='Settled', show_on=['form'], required=False),
        SelectField(
            'nesting',
            title='Nesting',
            show_on=['form'],
            required=False,
            choices=Nesting.choices,
            default_value=Nesting.POSSIBLY_NESTING,
        ),
        CheckboxField('nomadic', title='Nomadic', show_on=['form'], required=False),
        CheckboxField('wintering', title='Wintering', show_on=['form'], required=False),
        CheckboxField('spanning', title='Spanning', show_on=['form'], required=False),
        CheckboxField('straying', title='Straying', show_on=['form'], required=False),
        CheckboxField('dimorphism', title='Dimorphism', show_on=['form'], required=False),
        CheckboxField('waterfowl', title='Waterfowl', show_on=['form'], required=False),
        SelectField('red_book', title='Red book', required=False, choices=RedBook.choices),
        SelectField(
            'iucn_risk',
            title='IUCN risk',
            required=False,
            choices=IUCNRisk.choices,
            default_value=IUCNRisk.LEAST_CONCERN,
        ),
    ]

    async def choices_for_genus_id(self, request: Request) -> list[tuple[str, typing.Any]]:
        stmt = select(Genus).order_by(Genus.name_la)
        return await query(request.state.db).choices(stmt)

    async def validator_for_name_la(self, request: Request, form: Form, field: wtforms.Field) -> None:
        if field.object_data == field.data:
            return

        stmt = select(Specie).where(sa.func.lower(Specie.name_la) == field.data.lower())
        if await query(request.state.db).exists(stmt):
            raise wtforms.ValidationError('This value must be unique.')


this_dir = pathlib.Path(__file__).parent
admin = OhMyAdmin(
    database_url='postgresql+asyncpg://postgres:postgres@localhost/haj',
    user_menu_config=user_menu_config,
    template_dirs=[this_dir / 'templates'],
    tools=[Backup, FileManager, Calendar, Photos],
    dashboards=[OverviewDashboard],
    resources=[OrdersResource, FamiliesResource, GeneraResource, SpeciesResource],
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
