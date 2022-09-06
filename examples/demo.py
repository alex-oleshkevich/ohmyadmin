import pathlib
import sqlalchemy as sa
import typing
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
from ohmyadmin.helpers import render_to_response
from ohmyadmin.nav import MenuGroup, MenuItem
from ohmyadmin.tables import ActionGroup, BatchAction, Column, TableView

metadata = sa.MetaData()
Base = declarative_base()


class DeleteAllAction(BatchAction):
    id = 'delete'
    label = 'Delete all'
    confirmation = 'Do you want to delete all items?'
    dangerous = True

    async def apply(self, request: Request, ids: list[str], params: dict[str, str]) -> Response:
        return RedirectResponse(request.headers.get('referer') + "?done", 302)


class UserTable(TableView):
    id = 'users'
    label = 'Users'
    queryset = sa.select(User)
    columns = [
        Column('id', label='ID'),
        Column('first_name', label='First name', sortable=True, searchable=True),
        Column('last_name', label='Last name', sortable=True, searchable=True),
        Column('email', label='Email', searchable=True),
        Column('is_active', label='Active'),
    ]

    def table_actions(self, request: Request) -> typing.Iterable[Action]:
        return [
            LinkAction('Export', url='/admin', icon='download'),
            LinkAction(text='New user', url='/admin/users/create', icon='plus', color='primary'),
        ]

    def row_actions(self, request: Request, entity: typing.Any) -> typing.Iterable[Action]:
        return [
            ActionGroup(
                [
                    LinkAction('Impersonate', '/admin/edit', icon='eye'),
                    LinkAction('Deactivate', '/admin/edit', icon='eye'),
                    LinkAction('View', '/admin/view', icon='eye'),
                    LinkAction('Delete', '/admin/delete', icon='trash'),
                ]
            ),
            LinkAction('Edit', '/admin/edit', icon='pencil'),
        ]

    def batch_actions(self, request: Request) -> typing.Iterable[BatchAction]:
        return [
            DeleteAllAction(),
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
                ],
            ),
        ),
    ],
)
