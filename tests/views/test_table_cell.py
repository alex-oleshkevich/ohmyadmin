from starlette.datastructures import URL
from starlette.requests import Request
from starlette.testclient import TestClient

from ohmyadmin.datasources.datasource import DataSource
from ohmyadmin.helpers import LazyObjectURL, LazyURL
from ohmyadmin.ordering import SortingHelper
from ohmyadmin.pages.table import TablePage
from ohmyadmin.testing import MarkupSelector
from ohmyadmin.screens.table import TableColumn
from tests.conftest import CreateTestAppFactory
from tests.models import Post


def test_cell_generates_label() -> None:
    cell = TableColumn("first_name")
    assert cell.label == "First name"


def test_cell_search_in() -> None:
    cell = TableColumn("first_name", searchable=True)
    assert cell.search_in == "first_name"

    cell = TableColumn("first_name", search_in="last_name")
    assert cell.search_in == "last_name"


def test_cell_sort_by() -> None:
    cell = TableColumn("first_name", sortable=True)
    assert cell.sort_by == "first_name"

    cell = TableColumn("first_name", sort_by="last_name")
    assert cell.sort_by == "last_name"


def test_cell_gets_value(http_request: Request) -> None:
    cell = TableColumn("title")
    assert cell.get_value(Post(title="TITLE")) == "TITLE"


def test_cell_custom_value_getter(http_request: Request) -> None:
    cell = TableColumn("title", value_getter=lambda o: o.id)
    assert cell.get_value(Post(title="TITLE", id=100)) == 100


def test_cell_formats_value(http_request: Request) -> None:
    cell = TableColumn("first_name", formatter=lambda r, v: "FORMATTED-" + v)
    assert cell.format_value(http_request, "VALUE") == "FORMATTED-VALUE"


def test_cell_renders_cell(http_request: Request) -> None:
    model = Post(title="TITLE")
    cell = TableColumn("title")
    assert cell.render(http_request, model) == "TITLE"


def test_cell_renders_head_cell(http_request: Request) -> None:
    cell = TableColumn("title")
    http_request.state.table_sorting = SortingHelper(http_request, "ordering")
    assert str(cell.render_head_cell(http_request)) == "Title"


def test_cell_renders_sortable_head_cell(http_request: Request) -> None:
    cell = TableColumn("title", sortable=True)
    http_request.state.table_sorting = SortingHelper(http_request, "ordering")
    selector = MarkupSelector(cell.render_head_cell(http_request))
    assert selector.has_node("svg")
    assert selector.has_node("a")
    assert selector.get_attribute("a", "href") == "http://testserver/admin/?ordering=title"


def test_cell_renders_link(create_test_app: CreateTestAppFactory, datasource: DataSource) -> None:
    dataset = datasource

    class MyPage(TablePage):
        slug = "mypage"
        datasource = dataset
        columns = [TableColumn("title", link=True)]

    app = create_test_app(pages=[MyPage()])
    client = TestClient(app)
    response = client.get("/admin/mypage")
    selector = MarkupSelector(response.text)
    assert selector.has_node('[data-test="datatable"] tbody tr td:first-child a')
    assert selector.get_text('[data-test="datatable"] tbody tr td:first-child a') == "Title 1"
    assert (
        selector.get_attribute('[data-test="datatable"] tbody tr td:first-child a', "href")
        == "http://testserver/admin/mypage/"
    )


def test_cell_renders_lazy_link(create_test_app: CreateTestAppFactory, datasource: DataSource) -> None:
    dataset = datasource

    class MyPage(TablePage):
        slug = "mypage"
        datasource = dataset
        columns = [TableColumn("title", link=LazyURL("posts", path_params={"id": "100"}))]

    app = create_test_app(pages=[MyPage()])
    client = TestClient(app)
    response = client.get("/admin/mypage")
    selector = MarkupSelector(response.text)
    assert (
        selector.get_attribute('[data-test="datatable"] tbody tr td:first-child a', "href")
        == "http://testserver/posts/100"
    )


def test_cell_renders_lazy_object_link(create_test_app: CreateTestAppFactory, datasource: DataSource) -> None:
    dataset = datasource

    class MyPage(TablePage):
        slug = "mypage"
        datasource = dataset
        columns = [TableColumn("title", link=LazyObjectURL(factory=lambda r, o: URL("/to-object")))]

    app = create_test_app(pages=[MyPage()])
    client = TestClient(app)
    response = client.get("/admin/mypage")
    selector = MarkupSelector(response.text)
    assert selector.get_attribute('[data-test="datatable"] tbody tr td:first-child a', "href") == "/to-object"


def test_cell_renders_simple_link(create_test_app: CreateTestAppFactory, datasource: DataSource) -> None:
    dataset = datasource

    class MyPage(TablePage):
        slug = "mypage"
        datasource = dataset
        columns = [TableColumn("title", link="http://example.com")]

    app = create_test_app(pages=[MyPage()])
    client = TestClient(app)
    response = client.get("/admin/mypage")
    selector = MarkupSelector(response.text)
    assert selector.get_attribute('[data-test="datatable"] tbody tr td:first-child a', "href") == "http://example.com"
