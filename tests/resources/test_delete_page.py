import pytest
from starlette.testclient import TestClient

from ohmyadmin.testing import MarkupSelector


def test_renders_delete_page(client: TestClient) -> None:
    response = client.get("/admin/resources/demo/1/delete")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.has_node('form button[type="submit"].btn-danger')
    assert selector.has_node(
        'form a[href="http://testserver/admin/resources/demo/"].btn-text'
    )


@pytest.mark.parametrize("method", ["post", "delete"])
def test_dispatches(client: TestClient, method: str) -> None:
    callback = getattr(client, method)
    response = callback("/admin/resources/demo/1/delete", allow_redirects=False)
    assert response.status_code == 302


@pytest.mark.parametrize("method", ["post", "delete"])
def test_dispatches_htmx(client: TestClient, method: str) -> None:
    callback = getattr(client, method)
    response = callback(
        "/admin/resources/demo/1/delete",
        allow_redirects=False,
        headers={"hx-request": "true"},
    )
    assert response.status_code == 204
