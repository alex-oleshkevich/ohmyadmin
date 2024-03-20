from starlette.authentication import AuthenticationBackend, BaseUser
from starlette.requests import HTTPConnection, Request
from starlette.testclient import TestClient

from ohmyadmin.app import OhMyAdmin
from ohmyadmin.authentication import AnonymousAuthPolicy, AuthPolicy, SESSION_KEY, SessionAuthBackend
from tests.auth import AuthTestPolicy
from tests.conftest import RequestFactory
from tests.models import User


def test_login_page() -> None: ...


def test_logout_page() -> None: ...


async def test_auth_policy(request: Request, user: User) -> None:
    policy = AuthTestPolicy(user)
    assert await policy.load_user(request, str(user.id)) == user


async def test_anonymous_auth_policy(request_f: RequestFactory) -> None:
    request = request_f()
    policy = AnonymousAuthPolicy()
    assert await policy.load_user(request, "1")
    assert await policy.authenticate(request, "root@localhost", "password") is None


async def test_login_accessible(client: TestClient, user: User) -> None:
    response = client.get("/admin/login")
    assert response.status_code == 200


async def test_login_success(client: TestClient, user: User) -> None:
    response = client.post("/admin/login", data={"identity": user.email, "password": "password"})
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/admin/"


async def test_login_invalid_credentials(client: TestClient, user: User) -> None:
    response = client.post("/admin/login", data={"identity": user.email, "password": "invalid"})
    assert response.status_code == 200


async def test_login_redirects_to_next_url(client: TestClient, user: User) -> None:
    response = client.post(
        "/admin/login?next=/admin",
        data={
            "identity": user.email,
            "password": "password",
        },
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/admin"


async def test_logout(auth_client: TestClient, user: User) -> None:
    response = auth_client.get("/admin/logout")
    assert response.status_code == 405

    response = auth_client.post("/admin/logout")
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/admin/login"


async def test_session_backend(ohmyadmin: OhMyAdmin, request_f: RequestFactory) -> None:
    class TestPolicy(AuthPolicy):
        async def authenticate(
            self, request: Request, identity: str, password: str
        ) -> BaseUser | None:  # pragma: no cover
            return None

        async def load_user(self, conn: HTTPConnection, user_id: str) -> BaseUser | None:  # pragma: no cover
            if user_id == "1":
                return User(id=1)
            return None

        def get_authentication_backend(
            self,
        ) -> AuthenticationBackend:  # pragma: no cover
            return SessionAuthBackend()

    ohmyadmin.auth_policy = TestPolicy()
    request = request_f(state={"app": ohmyadmin}, session={SESSION_KEY: "2"})
    backend = SessionAuthBackend()
    result = await backend.authenticate(request)
    assert result
    creds, user = result
    assert not user.is_authenticated

    request = request_f(state={"app": ohmyadmin}, session={SESSION_KEY: "1"})
    backend = SessionAuthBackend()
    result = await backend.authenticate(request)
    assert result
    creds, user = result
    assert user.is_authenticated
