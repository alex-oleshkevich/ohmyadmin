import datetime
import pathlib
import pytest
import typing
from async_storages import FileStorage, MemoryStorage
from starlette.applications import Starlette
from starlette.authentication import AuthCredentials, BaseUser
from starlette.datastructures import FormData
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route

from ohmyadmin.app import OhMyAdmin
from ohmyadmin.authentication import BaseAuthPolicy
from ohmyadmin.datasource.memory import InMemoryDataSource
from ohmyadmin.menu import NavItem
from ohmyadmin.pages.base import BasePage
from tests.models import Post
from tests.utils import AuthTestPolicy


class CreateTestAppFactory(typing.Protocol):  # pragma: no cover
    def __call__(
        self,
        pages: typing.Sequence[BasePage] | None = None,
        user_menu: typing.Sequence[NavItem] | None = None,
        auth_policy: BaseAuthPolicy | None = None,
    ) -> Starlette:
        ...


@pytest.fixture()
def extra_template_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    yield tmp_path


@pytest.fixture()
def file_storage() -> FileStorage:
    return FileStorage(MemoryStorage())


@pytest.fixture()
def auth_policy() -> BaseAuthPolicy:
    return AuthTestPolicy()


@pytest.fixture
def admin(extra_template_dir: pathlib.Path) -> OhMyAdmin:
    return OhMyAdmin(
        title='test',
        logo_url='http://example.com',
        template_dir=extra_template_dir,
    )


@pytest.fixture
def create_test_app(
    extra_template_dir: pathlib.Path, file_storage: FileStorage, auth_policy: BaseAuthPolicy
) -> CreateTestAppFactory:
    default_auth_policy = auth_policy

    def factory(
        pages: typing.Sequence[BasePage] | None = None,
        user_menu: typing.Sequence[NavItem] | None = None,
        auth_policy: BaseAuthPolicy | None = None,
    ) -> Starlette:
        admin = OhMyAdmin(
            pages=pages,
            auth_policy=auth_policy or default_auth_policy,
            file_storage=file_storage,
            template_dir=extra_template_dir,
            user_menu=user_menu,
        )
        return Starlette(
            routes=[
                Mount('/admin', admin),
                Route('/users', Response('ok'), name='users'),
                Route('/posts/{id}', Response('ok'), name='posts'),
            ],
            middleware=[
                Middleware(SessionMiddleware, secret_key='key!'),
            ],
        )

    return factory


class RequestFactory(typing.Protocol):
    def __call__(
        self,
        https: bool = False,
        path: str = '/admin',
        host: str = 'testserver',
        query_string: str = '',
        root_path: str = '/admin',
        method: str = 'GET',
        auth: AuthCredentials | None = None,
        user: BaseUser | None = None,
        routes: typing.Sequence[BaseRoute] | None = None,
        state: dict[str, typing.Any] | None = None,
        session: dict[str, typing.Any] | None = None,
        form_data: dict[str, typing.Any] | FormData | None = None,
    ) -> Request:
        ...  # pragma: no cover


@pytest.fixture
def request_f(admin: OhMyAdmin) -> typing.Callable[[], Request]:
    def http_request(
        https: bool = False,
        path: str = '/',
        host: str = 'testserver',
        query_string: str = '',
        root_path: str = '/admin',
        method: str = 'GET',
        auth: AuthCredentials | None = None,
        user: BaseUser | None = None,
        routes: typing.Sequence[BaseRoute] | None = None,
        state: dict[str, typing.Any] | None = None,
        session: dict[str, typing.Any] | None = None,
        form_data: dict[str, typing.Any] | FormData | None = None,
    ) -> Request:
        """
        Create a fake request class.

        Note, `root_path` is set to `/admin` to simulate a case when admin app is mounted using Mount().
        """

        if isinstance(form_data, dict):
            form_data = FormData(form_data)

        app = Starlette(
            routes=routes
            or [
                Mount('/', Response('ok'), name='ohmyadmin.welcome'),
                Mount('/static', Response('ok'), name='ohmyadmin.static'),
                Mount('/media', Response('ok'), name='ohmyadmin.media'),
            ]
        )
        state = state or {}
        state.setdefault('admin', admin)
        state.setdefault('app', app)
        scope = {
            'type': 'http',
            'version': '3.0',
            'spec_version': '2.3',
            'http_version': '1.1',
            'server': ('127.0.0.1', 7002),
            'client': ('127.0.0.1', 49880),
            'path': path,
            'raw_path': (root_path + path).encode(),
            'root_path': root_path,
            'scheme': 'https' if https else 'http',
            'headers': [
                (b'host', host.encode()),
            ],
            'method': method,
            'session': session or {},
            'path_params': {},
            'query_string': query_string.encode(),
            'state': state,
            'auth': auth,
            'user': user,
            'app': app,
            'router': app.router,
        }
        request = Request(scope)
        if form_data:
            setattr(request, '_form', form_data)
        return request

    return http_request


@pytest.fixture
def http_request(request_f: RequestFactory, datasource: InMemoryDataSource) -> Request:
    return request_f(
        routes=[
            Route('/users', Response('ok'), name='users'),
            Route('/posts/{id}', Response('ok'), name='posts'),
            Mount('/media', Response('ok'), name='ohmyadmin.media'),
        ],
        state={
            'datasource': datasource,
        },
    )


@pytest.fixture
def datasource() -> InMemoryDataSource[Post]:
    return InMemoryDataSource(
        Post,
        [
            Post(
                id=index,
                title=f'Title {index}',
                published=index % 5 == 0,
                date_published=datetime.date(2023, 1, index),
                updated_at=datetime.datetime(2023, 1, index, 12, 0, 0),
            )
            for index in range(1, 21)
        ],
    )
