import pathlib
import sqlalchemy as sa
import typing
import wtforms
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Mount, Route

from examples.models import User
from ohmyadmin.actions import Action, LinkAction
from ohmyadmin.app import OhMyAdmin, UserMenu
from ohmyadmin.forms import (
    CheckboxField,
    DateField,
    DateTimeField,
    DecimalField,
    DecimalRangeField,
    EmailField,
    EmbedField,
    EmbedManyField,
    Field,
    FileField,
    FloatField,
    Form,
    FormView,
    Grid,
    HiddenField,
    IntegerField,
    IntegerRangeField,
    Layout,
    ListField,
    MonthField,
    MultipleFileField,
    PasswordField,
    RadioField,
    SelectField,
    SelectMultipleField,
    TelField,
    TextareaField,
    TextField,
    TimeField,
    URLField,
)
from ohmyadmin.helpers import render_to_response
from ohmyadmin.nav import MenuGroup, MenuItem
from ohmyadmin.tables import ActionGroup, BatchAction, Column, TableView

metadata = sa.MetaData()
Base = declarative_base()


class DeleteAllAction(BatchAction):
    id = 'delete'
    label = 'Delete all'
    dangerous = True
    confirmation = 'Do you want to delete all items?'

    async def apply(self, request: Request, ids: list[str], params: dict[str, str]) -> Response:
        return RedirectResponse(request.headers.get('referer'), 302)


class UserTable(TableView):
    id = 'users'
    label = 'Users'
    queryset = sa.select(User)
    columns = [
        Column('id', label='ID'),
        Column(
            'full_name',
            label='Name',
            sortable=True,
            searchable=True,
            search_in=['first_name', 'last_name'],
            sort_by='last_name',
            link_factory=lambda r, o: '/admin/example-table?from-link',
        ),
        Column('email', label='Email', searchable=True),
        Column('is_active', label='Active'),
    ]

    def table_actions(self, request: Request) -> typing.Iterable[Action]:
        return [
            LinkAction('/admin', 'Export', icon='download'),
            LinkAction('/admin/users/create', 'New user', icon='plus', color='primary'),
        ]

    def row_actions(self, request: Request, entity: typing.Any) -> typing.Iterable[Action]:
        return [
            ActionGroup(
                [
                    LinkAction('/admin/edit', 'Impersonate'),
                    LinkAction('/admin/edit', 'Deactivate'),
                    LinkAction('/admin/edit', 'Preview'),
                    LinkAction('/admin/edit', 'Export as CSV'),
                    LinkAction('/admin/edit', 'Transfer License'),
                    LinkAction('/admin/view', 'View', icon='eye'),
                    LinkAction('/admin/delete', 'Delete', icon='trash', color='danger'),
                ]
            ),
            LinkAction('/admin/edit', 'Edit', icon='pencil'),
            LinkAction('/admin/delete', icon='trash', color='danger'),
        ]

    def batch_actions(self, request: Request) -> typing.Iterable[BatchAction]:
        return [
            DeleteAllAction(),
        ]


def not_root_validator(form: wtforms.Form, field: wtforms.Field) -> None:
    if field.data == 'root':
        raise wtforms.ValidationError('root cannot be used')


async def not_admin_validator(form: wtforms.Form, field: wtforms.Field) -> None:
    if field.data == 'admin':
        raise wtforms.ValidationError('admin cannot be used')


def sync_user_choices():
    return [('1', 'Alex'), ('2', 'Jenny')]


async def async_user_choices():
    return [('1', 'Alex'), ('2', 'Jenny')]


class UserForm(FormView):
    def get_layout(self) -> list[Layout]:
        return [
            Field('field', label='Base field'),
            TextField(
                'first_name',
                label='First name',
                required=True,
                help_text="Summaries can't contain Markdown or HTML contents; only plain text.",
                validators=[not_root_validator, not_admin_validator],
            ),
            TextField('last_name', label='Last name'),
            FileField('photo', label='Photo'),
            MultipleFileField('documents'),
            EmbedField(
                'embed',
                [
                    TextField(
                        'first_name',
                        label='First name',
                        help_text="Summaries can't contain Markdown or HTML contents; only plain text.",
                        validators=[not_root_validator, not_admin_validator],
                    ),
                    TextField('last_name', label='Last name'),
                    PasswordField('password', label='Password', autocomplete='off'),
                ],
                cols=3,
            ),
            ListField('list_text', TextField('_')),
            EmbedManyField(
                'embed_many',
                [
                    TextField(
                        'first_name',
                        label='First name',
                        help_text="Summaries can't contain Markdown or HTML contents; only plain text.",
                        validators=[not_root_validator, not_admin_validator],
                    ),
                    TextField('last_name', label='Last name'),
                    SelectField('select', label='Static choices', choices=[('1', 'Alex'), ('2', 'Jenny')]),
                ],
            ),
            EmailField('email', label='Email', autocomplete='email', placeholder='Current email'),
            PasswordField('password', label='Password', autocomplete='off'),
            CheckboxField('is_active', label='Is active?'),
            TextareaField('description', label='Bio'),
            SelectField('select', label='Static choices', choices=[('1', 'Alex'), ('2', 'Jenny')]),
            SelectField('select2', label='Sync choices', choices=sync_user_choices),
            URLField('website', label='Website'),
            IntegerField('age', label='Age', min=0, max=100, step=1, default=0),
            DecimalField('salary', label='Salary', min=100, max=1000.50, step=100, default=1000),
            FloatField('score', label='Score', default=3.5),
            TelField('phone', label='Phone'),
            IntegerRangeField('number_range', label='Integer range'),
            DecimalRangeField('decimal_range', label='Decimal range'),
            HiddenField('hidden', label='Hidden'),
            DateTimeField('date_time', label='Date time'),
            DateField('date', label='Date'),
            TimeField('time', label='Time'),
            MonthField('month', label='Month'),
            SelectMultipleField('select_many', label='Static choices', choices=[('1', 'Alex'), ('2', 'Jenny')]),
            SelectMultipleField('select_many2', label='Sync choices', choices=sync_user_choices),
            RadioField('radio', label='Static choices', choices=[('1', 'Alex'), ('2', 'Jenny')]),
            RadioField('radio2', label='Sync choices', choices=sync_user_choices),
        ]


def index_view(request: Request) -> Response:
    url = request.url_for('welcome')
    return Response(f'<a href="{url}">admin</a>')


def example_page(request: Request) -> Response:
    return request.state.admin.render_to_response(
        request,
        'example.html',
        {
            'page_title': 'Example page',
        },
    )


def actions_overview(request: Request) -> Response:
    return render_to_response(
        request,
        'actions.html',
        {
            'actions': [
                LinkAction('Link', '#'),
                LinkAction('Link with icon', '#', icon='pencil'),
                LinkAction('Button link', '#', icon='pencil', color='default'),
                LinkAction('Primary button link', '#', icon='pencil', color='primary'),
                LinkAction('Danger button link', '#', icon='pencil', color='danger'),
            ]
        },
    )


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
            MenuItem.to_url('Overview', '/', icon='home'),
            MenuItem.to_url('Dashboard', '/', icon='dashboard'),
            MenuGroup(
                'Resources',
                [
                    MenuItem.to_url('Users', '/', icon='users'),
                    MenuItem.to_url('Role', '/', icon='fingerprint'),
                    MenuItem.to_url('News', '/', icon='article'),
                ],
            ),
            MenuGroup(
                'Docs',
                [
                    MenuItem.to_url('Library docs', '/'),
                    MenuItem.to_url('API docs', '/'),
                ],
            ),
            MenuGroup(
                'Pages',
                [
                    MenuItem.to_route('Example page', 'example_page'),
                    MenuItem.to_route('Example table', 'UserTable'),
                    MenuItem.to_route('Example form', 'UserForm'),
                    MenuItem.to_route('Actions', 'actions'),
                ],
            ),
        ]


this_dir = pathlib.Path(__file__).parent
engine = create_async_engine('postgresql+asyncpg://root:postgres@localhost/ohmyadmin', future=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

app = Starlette(
    debug=True,
    middleware=[
        Middleware(SessionMiddleware, secret_key='key!', path='/'),
    ],
    routes=[
        Route('/', index_view),
        Mount(
            '/admin',
            Admin(
                template_dirs=[this_dir / 'templates'],
                routes=[
                    Route('/example-page', example_page),
                    Route('/actions', actions_overview, name='actions'),
                    Route('/example-table', UserTable(dbsession=async_session)),
                    Route('/example-form', UserForm(dbsession=async_session)),
                ],
            ),
        ),
    ],
)
