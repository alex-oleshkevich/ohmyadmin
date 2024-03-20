from starlette.requests import Request
from starlette.testclient import TestClient

from ohmyadmin.authentication import AnonymousAuthPolicy
from tests.auth import AuthTestPolicy
from tests.conftest import RequestFactory
from tests.models import User


def test_login_page() -> None: ...


def test_logout_page() -> None: ...


async def test_auth_policy(http_get: Request, user: User) -> None:
    policy = AuthTestPolicy(user)
    assert await policy.load_user(http_get, str(user.id)) == user


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


async def test_logout(client: TestClient, user: User) -> None:
    response = client.get("/admin/logout")
    assert response.status_code == 405

    response = client.post("/admin/logout")
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/admin/login"
