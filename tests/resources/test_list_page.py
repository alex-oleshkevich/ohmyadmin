from starlette.testclient import TestClient

from ohmyadmin.testing import MarkupSelector
from tests.conftest import CreateTestAppFactory
from tests.resources.demo_resource import DemoResource


def test_renders_table(client: TestClient) -> None:
    response = client.get("/admin/resources/demo")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.has_node('[data-test="datatable"]')
    assert selector.count('[data-test="datatable"] tbody tr') == 25


def test_renders_links(client: TestClient) -> None:
    response = client.get("/admin/resources/demo")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.has_node('[data-test="datatable"]')
    assert selector.has_node('[data-test="datatable"] tbody tr td:nth-child(2) a')


def test_respects_page_size_param(client: TestClient) -> None:
    response = client.get("/admin/resources/demo?page_size=10")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.has_node('[data-test="datatable"]')
    assert selector.count('[data-test="datatable"] tbody tr') == 10


def test_respects_max_page_size_param(create_test_app: CreateTestAppFactory) -> None:
    class MyResource(DemoResource):
        slug = "demo"
        max_page_size = 10

    app = create_test_app(pages=[MyResource()])
    client = TestClient(app)

    response = client.get("/admin/resources/demo?page_size=20")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.has_node('[data-test="datatable"]')
    assert selector.count('[data-test="datatable"] tbody tr') == 10


def test_paginates(client: TestClient) -> None:
    response = client.get("/admin/resources/demo?page=2")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.has_node('[data-test="datatable"]')
    assert (
        selector.get_text(
            '[data-test="datatable"] tbody tr:nth-child(1) td:nth-child(2)'
        )
        == "Title 26"
    )


def test_renders_pagination(client: TestClient) -> None:
    response = client.get("/admin/resources/demo")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.has_node('[data-test="pagination"]')
    assert (
        selector.count('[data-test="pagination"] [data-test="pagination-control"]') == 4
    )  # 100 in dataset, 25 per page


def test_sorts_dataset(client: TestClient) -> None:
    response = client.get("/admin/resources/demo?ordering=-title")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert (
        selector.get_text(
            '[data-test="datatable"] tbody tr:first-child td:nth-child(2)'
        )
        == "Title 99"
    )


def test_renders_filters(client: TestClient) -> None:
    response = client.get("/admin/resources/demo")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.count('[data-test="filters-bar"] > *') == 1
    assert selector.get_text('[data-test="filters-bar"] button:first-child') == "Title"


def test_filters_dataset(client: TestClient) -> None:
    response = client.get(
        "/admin/resources/demo?title-query=Title%2099&title-operation=exact"
    )
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.count('[data-test="datatable"] tbody tr') == 1


def test_search_dataset(client: TestClient) -> None:
    response = client.get("/admin/resources/demo?search=Title%2099")
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.count('[data-test="datatable"] tbody tr') == 1
