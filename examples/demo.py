import pathlib
import sqlalchemy as sa
import typing
import wtforms
from sqlalchemy import select
from sqlalchemy.orm import declarative_base, declared_attr, joinedload, relationship, selectinload
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starsessions import SessionMiddleware

from ohmyadmin.admin import OhMyAdmin
from ohmyadmin.choices import TextChoices
from ohmyadmin.dashboards import Dashboard
from ohmyadmin.fields import (
    CheckboxField,
    Field,
    IntegerSelectField,
    MultiSelectField,
    SelectField,
    SubFormListField,
    TextareaField,
)
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


class BeakShape(TextChoices):
    TRIANGLE = 'triangle'
    CURVED_DOWN = 'curved_down'
    CURVED_UP = 'curved_up'
    FLAT = 'flat'


class BeakLength(TextChoices):
    SHORT = 'short'
    MEDIUM = 'medium'
    LONG = 'long'


class BeakThickness(TextChoices):
    THIN = 'thin'
    MEDIUM = 'medium'
    THICK = 'thick'


class Season(TextChoices):
    WINTER = 'winter'
    SPRING = 'spring'
    SUMMER = 'summer'
    AUTUMN = 'autumn'


class BodySize(TextChoices):
    SPARROW = 'sparrow'
    THRUSH = 'thrush'
    PIDGEON = 'pidgeon'
    DUCK = 'duck'
    LARGER = 'larger'


class Biotope(TextChoices):
    TOWN = 'town'
    FOREST = 'forest'
    FIELD = 'field'
    MEADOW = 'meadow'
    WATER = 'water'
    SWAMP = 'swamp'


class Color(TextChoices):
    BLACK = 'black'
    WHITE = 'white'
    GRAY = 'gray'
    CREAM = 'cream'
    YELLOW = 'yellow'
    ORANGE = 'orange'
    RED = 'red'
    BROWN = 'brown'
    VIOLET = 'violet'
    BLUE = 'blue'
    GREEN = 'green'


class Nesting(TextChoices):
    NOT_NESTING = 'not_nesting'
    NESTING = 'nesting'
    POSSIBLY_NESTING = 'possibly_nesting'


class Behavior(TextChoices):
    FLOATING = 'floating'
    AT_FEEDER = 'at_feeder'
    AT_GROUND = 'at_ground'
    HANGS_UP = 'hangs_up'
    FEEDS_IN_FLY = 'feeds_in_fly'
    EATS_BERRIES = 'eats_berries'
    EATS_ANIMALS = 'eats_animals'
    IN_FLOCK = 'in_flock'
    SHAKES_TAIL = 'shakes_tail'
    WALKING = 'walking'
    DIVING = 'diving'


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

    description = sa.Column(sa.Text, nullable=False, default="", server_default="")  # ?????????????? ??????
    # appearance = sa.Column(sa.Text, nullable=False, default="", server_default="")  # ?????????????? ??????
    # distribution = sa.Column(sa.Text, nullable=False, default="", server_default="")  # ??????????????????????????????
    # voice = sa.Column(sa.Text, nullable=False, default="", server_default="")  # ??????????
    # biotope = sa.Column(sa.Text, nullable=False, default="", server_default="")  # ?????????? ????????????????
    # nutrition = sa.Column(sa.Text, nullable=False, default="", server_default="")
    # biology = sa.Column(sa.Text, nullable=False, default="", server_default="")
    # interesting_facts = sa.Column(sa.Text, nullable=False, default="", server_default="")
    # threat_factors = sa.Column(sa.Text, nullable=False, default="", server_default="")  # ???????????????? ?????????????? ????????????
    comment = sa.Column(sa.Text, nullable=False, default="", server_default="")
    sources = sa.Column(sa.Text, nullable=False, default="", server_default="")  # information sources

    migratory = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)  # ????????????????????
    transiting = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)  # ?????????????????? ?????????????????????? ??????
    settled = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)  # ??????????????
    nesting = sa.Column(sa.String, nullable=False, default=False)
    """??????????????????????, ???????? ????????, ?? ???????????????????? ?? ???????????????? ?????????????? ????????????????????????."""
    nomadic = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)  # ????????????????
    wintering = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)
    """????????????????, ????????, ???? ???????????????????????????? ?? ???????????????? ??????????????, ???? ?????????????????? ?????????????????????????? ?? ???????????? ????????????."""
    spanning = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)
    """??????????????????, ????????, ???????????????????????? ?? ???????????????? ?????????????? ???? ?????????? ???????????????? (??????????????, ??????????????)
    ?? ?????????????????????? ???????????? ?????? ???? ?????????? ????????."""
    straying = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)
    """????????????????, ????????, ???????????????? ?????????????????????? ???? ???????????????????? ?????????????? ???? ??????????-???? ????????????????,
    ?????????????????? ???????? ?? ?????????? ?????????????????????? ?????????????? ?????????????????? ???????????? ???? ?????????????????? ??????????????."""
    dimorphism = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)
    waterfowl = sa.Column(sa.Boolean, nullable=False, server_default='0', default=False)
    red_book = sa.Column(sa.String)
    iucn_risk = sa.Column(sa.String, nullable=False)
    genus_id = sa.Column(sa.ForeignKey("genea.id"), nullable=False)
    genus = relationship(Genus, cascade='save-update')

    appearances = relationship('Appearance', cascade='all,delete-orphan')
    photos = relationship('Photo', cascade='all,delete-orphan')
    videos = relationship('Video', cascade='all,delete-orphan')
    voices = relationship('Voice', cascade='all,delete-orphan')

    @property
    def name(self) -> str:
        if self.name_ru:
            return f'{self.name_ru} ({self.name_la})'
        return self.name_la

    def __str__(self) -> str:
        return self.name_be


class Appearance(Base):
    __tablename__ = 'specie_appearances'
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    beak_shape = sa.Column(sa.JSON, server_default='[]', default=list)
    beak_length = sa.Column(sa.String(128))
    beak_thickness = sa.Column(sa.String(128))
    body_size = sa.Column(sa.String(128))

    leg_colors = sa.Column(sa.JSON, nullable=True, server_default='[]', default=list)
    beak_colors = sa.Column(sa.JSON, nullable=True, server_default='[]', default=list)
    behaviors = sa.Column(sa.JSON, nullable=True, server_default='[]', default=list)
    seasons = sa.Column(sa.JSON, nullable=True, server_default='[]', default=list)
    habitats = sa.Column(sa.JSON, nullable=True, server_default='[]', default=list)
    colors = sa.Column(sa.JSON, nullable=True, server_default='[]', default=list)

    gender = sa.Column(sa.String(128))
    age = sa.Column(sa.String(128))
    specie_id = sa.Column(sa.ForeignKey("species.id"), nullable=False)


class Media(Base):
    __abstract__ = True
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    path = sa.Column(sa.String(512), nullable=False)
    author = sa.Column(sa.String(512), nullable=False)
    gender = sa.Column(sa.String(32))
    age = sa.Column(sa.String(32))
    created_at = sa.Column(sa.DateTime(timezone=True))

    @declared_attr
    def uploader_id(self):
        return sa.Column(sa.ForeignKey("users.id"), nullable=False)

    @declared_attr
    def specie_id(self):
        return sa.Column(sa.ForeignKey("species.id"), nullable=False)


class Photo(Media):
    __tablename__ = 'photos'


class Video(Media):
    __tablename__ = 'videos'


class Gender(TextChoices):
    UNKNOWN = 'unknown'
    MALE = 'male'
    FEMALE = 'female'


class Age(TextChoices):
    UNKNOWN = 'unknown'
    ADULT = 'adult'
    IMMATURE = 'immature'
    JUVENILE = 'juvenile'


class VoiceType(TextChoices):
    UNKNOWN = 'unknown'
    SONG = 'song'
    CALL = 'call'
    NON_VOCAL = 'non_vocal'


class Voice(Base):
    __tablename__ = 'voices'
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    path = sa.Column(sa.String(512), nullable=False)
    description = sa.Column(sa.String(512), default='')
    gender = sa.Column(sa.String(32), default=Gender.UNKNOWN)
    type = sa.Column(sa.String(32), default=VoiceType.SONG)
    age = sa.Column(sa.String(32), default=Age.UNKNOWN)
    created_at = sa.Column(sa.DateTime(timezone=True), default=sa.func.now)

    uploader_id = sa.Column(sa.ForeignKey("users.id"), nullable=False)
    specie_id = sa.Column(sa.ForeignKey("species.id"), nullable=False)


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
            selectinload(Specie.photos),
            selectinload(Specie.videos),
            selectinload(Specie.voices),
            selectinload(Specie.appearances),
        )
    )
    fields = [
        Field('name_ru', title='Name (rus)', searchable=True, sortable=True, link=True, required=False),
        Field('name_be', title='Name (bel)', searchable=True, show_on=['form'], required=False),
        Field('name_en', title='Name (eng)', searchable=True, show_on=['form'], required=False),
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
        SubFormListField(
            'appearances',
            entity_class=Appearance,
            fields=[
                SelectField('beak_length', title='Beak length', choices=BeakLength.choices, required=False),
                SelectField('beak_thickness', title='Beak thickness', choices=BeakThickness.choices, required=False),
                SelectField('body_size', title='Body size', choices=BodySize.choices, required=False),
                MultiSelectField('beak_shape', title='Body shape', choices=BeakShape.choices, required=False),
                MultiSelectField('beak_colors', title='Body colors', choices=Color.choices, required=False),
                MultiSelectField('leg_colors', title='Leg colors', choices=Color.choices, required=False),
                MultiSelectField('behaviors', title='Behaviors', choices=Behavior.choices, required=False),
                MultiSelectField('seasons', title='Seasons', choices=Season.choices, required=False),
                MultiSelectField('habitats', title='Biotope', choices=Biotope.choices, required=False),
                MultiSelectField('colors', title='Colors', choices=Color.choices, required=False),
                SelectField('age', title='Age', choices=Age.choices, default_value=Age.ADULT, required=False),
                SelectField(
                    'gender', title='Gender', choices=Gender.choices, default_value=Gender.UNKNOWN, required=False
                ),
            ],
        ),
    ]

    async def choices_for_genus_id(self, request: Request) -> list[tuple[str, typing.Any]]:
        stmt = select(Genus).order_by(Genus.name_la)
        return await query(request.state.db).choices(stmt)

    async def validator_for_name_la(self, form: Form, field: wtforms.Field) -> None:
        if field.object_data == field.data:
            return

        stmt = select(Specie).where(sa.func.lower(Specie.name_la) == field.data.lower())
        if await query(form.request.state.db).exists(stmt):
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
