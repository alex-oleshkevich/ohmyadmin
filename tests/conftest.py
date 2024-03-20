import pathlib
import typing

import pytest
from async_storages import FileStorage, MemoryBackend
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.routing import Mount
from starlette.testclient import TestClient

from ohmyadmin.app import OhMyAdmin
from ohmyadmin.authentication import AuthPolicy
from tests.auth import AuthTestPolicy
from tests.factories import UserFactory
from tests.models import User


@pytest.fixture
def user() -> User:
    return UserFactory.build()


@pytest.fixture()
def file_storage() -> FileStorage:
    return FileStorage(MemoryBackend())


@pytest.fixture()
def auth_policy(user: User) -> AuthPolicy:
    return AuthTestPolicy(user)


@pytest.fixture
def template_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    yield tmp_path


@pytest.fixture
def ohmyadmin(
    auth_policy: AuthPolicy,
    file_storage: FileStorage,
    template_dir: pathlib.Path,
) -> OhMyAdmin:
    return OhMyAdmin(
        pages=[],
        file_storage=file_storage,
        auth_policy=auth_policy,
        template_dirs=[template_dir],
    )


AppFactory = typing.Callable[[OhMyAdmin], Starlette]


@pytest.fixture
def app_f() -> AppFactory:
    def factory(admin_app: OhMyAdmin) -> Starlette:
        return Starlette(
            routes=[Mount("/admin", app=admin_app)],
            middleware=[
                Middleware(SessionMiddleware, secret_key="key!", path="/"),
            ],
        )

    return factory


@pytest.fixture
def app(app_f: AppFactory, ohmyadmin: OhMyAdmin) -> Starlette:
    return app_f(ohmyadmin)


class RequestFactory(typing.Protocol):  # pragma: no cover:
    def __call__(self, method: str = "get", type: str = "http") -> Request: ...


@pytest.fixture
def request_f(ohmyadmin: OhMyAdmin) -> RequestFactory:
    def factory(
        method: str = "get",
        type: str = "http",
    ) -> Request:
        scope = {
            "type": type,
            "method": method,
            "state": {
                "ohmyadmin": ohmyadmin,
            },
        }
        return Request(scope)

    return factory


@pytest.fixture
def http_get(request_f: RequestFactory) -> Request:
    return request_f(method="get")


@pytest.fixture
def client(app: Starlette) -> typing.Generator[TestClient, None, None]:
    with TestClient(app, follow_redirects=False) as client:
        yield client
