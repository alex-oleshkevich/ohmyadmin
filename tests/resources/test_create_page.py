from starlette.testclient import TestClient

from ohmyadmin import actions
from ohmyadmin.testing import MarkupSelector
from tests.conftest import CreateTestAppFactory
from tests.resources.demo_resource import DemoResource


def test_renders_create_form(client: TestClient) -> None:
    response = client.get("/admin/resources/demo/new")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.has_node('form input[type="text"][name="title"]')


def test_validates_form(client: TestClient) -> None:
    response = client.post("/admin/resources/demo/new", data={"title": ""})
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.get_text("form .form-errors") == "This field is required."


def test_submits_form_and_edits(client: TestClient) -> None:
    response = client.post(
        "/admin/resources/demo/new", data={"title": "new title", "_edit": ""}
    )
    assert response.status_code == 204
    assert (
        response.headers["hx-redirect"]
        == "http://testserver/admin/resources/demo/1/edit"
    )


def test_submits_form_and_returns(client: TestClient) -> None:
    response = client.post(
        "/admin/resources/demo/new", data={"title": "new title", "_return": ""}
    )
    assert response.status_code == 204
    assert response.headers["hx-redirect"] == "http://testserver/admin/resources/demo/"


def test_submits_form_and_creates_new(client: TestClient) -> None:
    response = client.post(
        "/admin/resources/demo/new", data={"title": "new title", "_add_new": ""}
    )
    assert response.status_code == 204
    assert (
        response.headers["hx-redirect"] == "http://testserver/admin/resources/demo/new"
    )


def test_renders_form_actions(client: TestClient) -> None:
    response = client.get("/admin/resources/demo/new")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert (
        selector.get_text('form .form-actions button[type="submit"].btn-accent')
        == "Create and return to list"
    )
    assert (
        selector.get_text('form .form-actions button[type="submit"]:nth-child(2)')
        == "Create and edit"
    )
    assert (
        selector.get_text('form .form-actions button[type="submit"]:nth-child(3)')
        == "Create and add new"
    )


def test_renders_custom_form_actions(create_test_app: CreateTestAppFactory) -> None:
    class MyResource(DemoResource):
        slug = "demo"
        create_form_actions = [actions.Submit(label="Create")]

    app = create_test_app(pages=[MyResource()])
    client = TestClient(app)
    response = client.get("/admin/resources/demo/new")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.count("form .form-actions button") == 1
    assert (
        selector.get_text('form .form-actions button[type="submit"]:first-child')
        == "Create"
    )
