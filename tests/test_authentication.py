from starlette.authentication import AuthCredentials, AuthenticationBackend, BaseUser
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import HTTPConnection, Request
from starlette.testclient import TestClient
from starlette.types import Message
from unittest import mock

from ohmyadmin.app import OhMyAdmin
from ohmyadmin.authentication import SESSION_KEY, AnonymousAuthPolicy, AnonymousUser, BaseAuthPolicy, SessionAuthBackend
from ohmyadmin.middleware import LoginRequiredMiddleware
from ohmyadmin.pages.page import Page
from tests.conftest import CreateTestAppFactory, RequestFactory
from tests.models import User


async def test_anonymous_auth_policy() -> None:
    policy = AnonymousAuthPolicy()
    request = Request({'type': 'http'})
    assert not await policy.authenticate(request, 'anon', 'pass')
    assert isinstance(await policy.load_user(request, '1'), AnonymousUser)


async def test_session_backend(admin: OhMyAdmin, request_f: RequestFactory) -> None:
    class TestPolicy(BaseAuthPolicy):
        async def authenticate(
            self, request: Request, identity: str, password: str
        ) -> BaseUser | None:  # pragma: no cover
            return None

        async def load_user(self, conn: HTTPConnection, user_id: str) -> BaseUser | None:  # pragma: no cover
            if user_id == '1':
                return User(id='1')
            return None

        def get_authentication_backend(self) -> AuthenticationBackend:  # pragma: no cover
            return SessionAuthBackend()

    admin.auth_policy = TestPolicy()
    request = request_f(state={'admin': admin}, session={SESSION_KEY: '2'})
    backend = SessionAuthBackend()
    result = await backend.authenticate(request)
    assert result
    creds, user = result
    assert not user.is_authenticated

    request = request_f(state={'admin': admin}, session={SESSION_KEY: '1'})
    backend = SessionAuthBackend()
    result = await backend.authenticate(request)
    assert result
    creds, user = result
    assert user.is_authenticated


def test_pages_not_accessible_for_unauthenticated(create_test_app: CreateTestAppFactory) -> None:
    """Unauthenticated users should not be able to access pages."""

    class ExamplePage(Page):
        slug = 'example'

    app = create_test_app(pages=[ExamplePage()], auth_policy=AnonymousAuthPolicy())
    client = TestClient(app)
    response = client.get('/admin/example', allow_redirects=False)
    assert response.status_code == 302
    assert response.headers['location'] == 'http://testserver/admin/login?next=/admin/example'


def test_welcome_not_accessible_for_unauthenticated(create_test_app: CreateTestAppFactory) -> None:
    """Unauthenticated users should not be able to access welcome page."""

    app = create_test_app(pages=[], auth_policy=AnonymousAuthPolicy())
    client = TestClient(app)
    response = client.get('/admin/', allow_redirects=False)
    assert response.status_code == 302
    assert response.headers['location'] == 'http://testserver/admin/login?next=/admin/'


def test_media_not_accessible_for_unauthenticated(create_test_app: CreateTestAppFactory) -> None:
    """Unauthenticated users should not be able to access uploaded files."""

    app = create_test_app(pages=[], auth_policy=AnonymousAuthPolicy())
    client = TestClient(app)
    response = client.get('/admin/media/file.txt', allow_redirects=False)
    assert response.status_code == 302
    assert response.headers['location'] == 'http://testserver/admin/login?next=/admin/media/file.txt'


def test_login_is_accessible_for_unauthenticated(create_test_app: CreateTestAppFactory) -> None:
    """Unauthenticated users should not be able to access login page."""

    app = create_test_app(pages=[], auth_policy=AnonymousAuthPolicy())
    client = TestClient(app)
    response = client.get('/admin/login', allow_redirects=False)
    assert response.status_code == 200


def test_successful_login_logout(create_test_app: CreateTestAppFactory) -> None:
    """Test login logout flow (successful case)."""

    class UserPolicy(BaseAuthPolicy):  # pragma: no cover
        async def authenticate(self, request: Request, identity: str, password: str) -> BaseUser | None:
            if identity == 'valid@localhost.tld':
                return User(id='1')
            return None

        async def load_user(self, conn: HTTPConnection, user_id: str) -> BaseUser | None:
            if user_id == '1':
                return User(id='1')
            return None

    app = create_test_app(pages=[], auth_policy=UserPolicy())
    client = TestClient(app)
    response = client.post(
        '/admin/login', data={'identity': 'valid@localhost.tld', 'password': 'pass'}, allow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers['location'] == 'http://testserver/admin/'

    # access protected admin pages
    response = client.get('/admin')
    assert response.status_code == 200

    # perform logout
    response = client.post('/admin/logout', allow_redirects=False)
    assert response.status_code == 302
    assert response.headers['location'] == 'http://testserver/admin/login'

    # access protected admin pages
    response = client.get('/admin/', allow_redirects=False)
    assert response.status_code == 302
    assert response.headers['location'] == 'http://testserver/admin/login?next=/admin/'


def test_failed_login_logout(create_test_app: CreateTestAppFactory) -> None:
    """Test login logout flow (failing case)."""

    class UserPolicy(BaseAuthPolicy):  # pragma: no cover
        async def authenticate(self, request: Request, identity: str, password: str) -> BaseUser | None:
            if identity == 'valid@localhost.tld':
                return User(id='1')
            return None

        async def load_user(self, conn: HTTPConnection, user_id: str) -> BaseUser | None:
            if user_id == '1':
                return User(id='1')
            return None

    app = create_test_app(pages=[], auth_policy=UserPolicy())
    client = TestClient(app)
    response = client.post(
        '/admin/login', data={'identity': 'invalid@localhost.tld', 'password': 'pass'}, allow_redirects=False
    )
    assert response.status_code == 200  # stays at the same page

    # access protected admin pages
    response = client.get('/admin/', allow_redirects=False)
    assert response.status_code == 302
    assert response.headers['location'] == 'http://testserver/admin/login?next=/admin/'


async def test_login_required_middleware_checks_request_types() -> None:
    async def receive() -> Message:  # pragma: no cover
        return {}

    async def send(message: Message) -> None:  # pragma: no cover
        ...

    class DummyBackend(AuthenticationBackend):
        async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials, BaseUser] | None:
            return None

    child_app = mock.AsyncMock()
    app = SessionMiddleware(
        AuthenticationMiddleware(
            LoginRequiredMiddleware(app=child_app, exclude_paths=[]),
            backend=DummyBackend(),
        ),
        secret_key='key!',
    )
    await app({'type': 'unknown', 'headers': [], 'path': '/', 'router': mock.MagicMock()}, receive, send)
    child_app.assert_awaited_once()  # unsupported type - bypass

    child_app = mock.AsyncMock()
    app = SessionMiddleware(
        AuthenticationMiddleware(
            LoginRequiredMiddleware(app=child_app, exclude_paths=[]),
            backend=DummyBackend(),
        ),
        secret_key='key!',
    )
    await app({'type': 'http', 'headers': [], 'path': '/', 'router': mock.MagicMock()}, receive, send)
    child_app.assert_not_awaited()  # unauthenticated

    child_app = mock.AsyncMock()
    app = SessionMiddleware(
        AuthenticationMiddleware(
            LoginRequiredMiddleware(app=child_app, exclude_paths=[]),
            backend=DummyBackend(),
        ),
        secret_key='key!',
    )
    await app({'type': 'websocket', 'headers': [], 'path': '/', 'router': mock.MagicMock()}, receive, send)
    child_app.assert_not_awaited()  # unauthenticated
