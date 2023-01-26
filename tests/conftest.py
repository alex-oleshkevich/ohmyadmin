import pathlib
import pytest
import typing
from async_storages import FileStorage, MemoryStorage
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.routing import Mount

from ohmyadmin.app import OhMyAdmin
from ohmyadmin.authentication import BaseAuthPolicy
from ohmyadmin.menu import NavItem
from ohmyadmin.pages.base import BasePage
from tests.utils import AuthTestPolicy


@pytest.fixture
def admin() -> OhMyAdmin:
    return OhMyAdmin(title='test', logo_url='http://example.com')


class CreateTestAppFactory(typing.Protocol):
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
            routes=[Mount('/admin', admin)],
            middleware=[
                Middleware(SessionMiddleware, secret_key='key!'),
            ],
        )

    return factory


class RequestFactory(typing.Protocol):
    def __call__(self, https: bool = False, path: str = '/admin', host: str = 'testserver') -> Request:
        ...  # pragma: no cover


@pytest.fixture
def request_f(admin: OhMyAdmin) -> typing.Callable[[], Request]:
    def http_request(https: bool = False, path: str = '/admin', host: str = 'testserver') -> Request:
        return Request(
            {
                'type': 'http',
                'path': path,
                'scheme': 'https' if https else 'http',
                'headers': [
                    (b'host', host.encode()),
                ],
                'session': {},
                'state': {
                    'admin': admin,
                },
            }
        )

    return http_request
