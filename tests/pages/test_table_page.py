import datetime
from starlette.testclient import TestClient
from unittest import mock

from ohmyadmin import filters
from ohmyadmin.datasources.datasource import InMemoryDataSource
from ohmyadmin.pages.table import TablePage
from ohmyadmin.testing import MarkupSelector
from ohmyadmin.screens.table import TableColumn
from tests.conftest import CreateTestAppFactory
from tests.models import Post


class DummyTablePage(TablePage):
    slug = "dummy"
    page_size = 5
    datasource = InMemoryDataSource(
        Post,
        [Post(id=index, title=f"Post {index}", published=True) for index in range(20)],
    )
    columns = [
        TableColumn(name="id"),
        TableColumn(name="title"),
        TableColumn(name="published"),
    ]


class DummyTablePageWithSortableColumns(TablePage):
    slug = "dummy"
    datasource = InMemoryDataSource(
        Post,
        [Post(id=index, title=f"Post {index}", published=True) for index in range(20)],
    )
    columns = [
        TableColumn(name="id", sortable=True),
        TableColumn(name="title", sortable=True),
        TableColumn(name="published"),
    ]


class DummyTablePageWithSearchableColumns(TablePage):
    slug = "dummy"
    datasource = InMemoryDataSource(
        Post,
        [Post(id=index, title=f"Post {index}", published=True) for index in range(20)],
    )
    columns = [
        TableColumn(name="id"),
        TableColumn(name="title", searchable=True),
        TableColumn(name="published"),
    ]


class DummyTablePageWithFilters(TablePage):
    slug = "dummy"
    datasource = InMemoryDataSource(
        Post,
        [Post(id=index, title=f"Post {index}", published=True) for index in range(20)],
    )
    columns = [
        TableColumn(name="id"),
        TableColumn(name="title"),
        TableColumn(name="published"),
    ]
    filters = [
        filters.StringFilter("title"),
    ]


def test_page_accessible(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get("/admin/dummy")
    assert response.status_code == 200


def test_page_uses_specialized_query(create_test_app: CreateTestAppFactory) -> None:
    fn = mock.MagicMock()

    class SubDataSource(InMemoryDataSource):
        def get_query_for_index(self) -> InMemoryDataSource:
            fn()
            return self

    class DummyTable(TablePage):
        slug = "dummy"
        datasource = SubDataSource(Post, [Post(title=f"Post {index}") for index in range(20)])
        columns = [TableColumn(name="title")]
        filters = [filters.StringFilter("title")]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    client.get("/admin/dummy")
    fn.assert_called_once()


def test_renders_columns(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get("/admin/dummy")
    page = MarkupSelector(response.text)
    assert page.get_text("table thead tr th:nth-child(1)") == "Id"
    assert page.get_text("table thead tr th:nth-child(2)") == "Title"
    assert page.get_text("table thead tr th:nth-child(3)") == "Published"


def test_renders_sortable_columns(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePageWithSortableColumns()]))
    response = client.get("/admin/dummy")
    page = MarkupSelector(response.text)
    assert "ordering" in page.get_attribute("table thead tr th:first-child a", "href")


def test_not_renders_sortable_columns(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get("/admin/dummy")
    page = MarkupSelector(response.text)
    assert not page.has_node("table thead tr th:first-child a")


def test_renders_search_input(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePageWithSearchableColumns()]))
    response = client.get("/admin/dummy")
    page = MarkupSelector(response.text)
    assert page.has_node('input[type="search"][name="search"]')


def test_not_renders_search_input(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get("/admin/dummy")
    page = MarkupSelector(response.text)
    assert not page.has_node('input[type="search"][name="search"]')


def test_renders_pagination(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get("/admin/dummy")
    page = MarkupSelector(response.text)
    assert page.has_node('[data-test="pagination"]')


def test_renders_pagination_buttons(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get("/admin/dummy")
    page = MarkupSelector(response.text)
    assert page.get_text('[data-test="pagination-control"]:first-child') == "1"


def test_renders_filters(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePageWithFilters()]))
    response = client.get("/admin/dummy")
    page = MarkupSelector(response.text)
    assert page.has_node('[data-test="filters-trigger"]')
    assert page.has_node('[data-test="filters-bar"]')
    assert page.count('[data-test="filter"]') == 1


def test_not_renders_filters(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get("/admin/dummy")
    page = MarkupSelector(response.text)
    assert not page.has_node('[data-test="filters-trigger"]')


def test_performs_search(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePageWithSearchableColumns()]))
    response = client.get("/admin/dummy?search=Post 2")
    page = MarkupSelector(response.text)
    assert page.count('[data-test="datatable"] tbody tr') == 1
    assert "Post 2" in response.text


def test_performs_sorting(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePageWithSortableColumns()]))
    response = client.get("/admin/dummy?ordering=-title")
    page = MarkupSelector(response.text)
    assert page.get_text('[data-test="datatable"] tbody tr:first-child td:nth-child(2)') == "Post 9"
    assert page.get_text('[data-test="datatable"] tbody tr:nth-child(2) td:nth-child(2)') == "Post 8"


def test_applies_string_filter(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = "dummy"
        datasource = InMemoryDataSource(Post, [Post(title=f"Post {index}") for index in range(20)])
        columns = [TableColumn(name="title")]
        filters = [filters.StringFilter("title")]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get("/admin/dummy?title-query=19&title-operation=endswith")
    page = MarkupSelector(response.text)
    assert page.count('[data-test="datatable"] tbody tr') == 1
    assert page.get_text('[data-test="datatable"] tbody tr:first-child td:nth-child(1)') == "Post 19"


def test_applies_integer_filter(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = "dummy"
        datasource = InMemoryDataSource(Post, [Post(id=index) for index in range(20)])
        columns = [TableColumn(name="id")]
        filters = [filters.IntegerFilter("id")]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get("/admin/dummy?id-query=19&id-operation=eq")
    page = MarkupSelector(response.text)
    assert page.count('[data-test="datatable"] tbody tr') == 1
    assert page.get_text('[data-test="datatable"] tbody tr:first-child td:nth-child(1)') == "19"


def test_applies_float_filter(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = "dummy"
        datasource = InMemoryDataSource(Post, [Post(id=index) for index in range(20)])
        columns = [TableColumn(name="id")]
        filters = [filters.FloatFilter("id")]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get("/admin/dummy?id-query=19&id-operation=eq")
    page = MarkupSelector(response.text)
    assert page.count('[data-test="datatable"] tbody tr') == 1
    assert page.get_text('[data-test="datatable"] tbody tr:first-child td:nth-child(1)') == "19"


def test_applies_decimal_filter(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = "dummy"
        datasource = InMemoryDataSource(Post, [Post(id=index) for index in range(20)])
        columns = [TableColumn(name="id")]
        filters = [filters.DecimalFilter("id")]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get("/admin/dummy?id-query=19&id-operation=eq")
    page = MarkupSelector(response.text)
    assert page.count('[data-test="datatable"] tbody tr') == 1
    assert page.get_text('[data-test="datatable"] tbody tr:first-child td:nth-child(1)') == "19"


def test_applies_date_filter(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = "dummy"
        datasource = InMemoryDataSource(
            Post,
            [
                Post(date_published=datetime.date(2023, 1, 1)),
                Post(date_published=datetime.date(2023, 1, 2)),
            ],
        )
        columns = [TableColumn(name="date_published")]
        filters = [filters.DateFilter("date_published")]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get("/admin/dummy?date_published-query=2023-01-02")
    page = MarkupSelector(response.text)
    assert page.count('[data-test="datatable"] tbody tr') == 1
    assert page.get_text('[data-test="datatable"] tbody tr:first-child td:nth-child(1)') == "2023-01-02"


def test_applies_date_range_filter(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = "dummy"
        datasource = InMemoryDataSource(
            Post,
            [
                Post(date_published=datetime.date(2023, 1, 1)),
                Post(date_published=datetime.date(2023, 1, 2)),
                Post(date_published=datetime.date(2023, 1, 3)),
                Post(date_published=datetime.date(2023, 1, 4)),
            ],
        )
        columns = [TableColumn(name="date_published")]
        filters = [filters.DateRangeFilter("date_published")]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get("/admin/dummy?date_published-after=2023-01-02&date_published-before=2023-01-03")
    page = MarkupSelector(response.text)
    assert page.count('[data-test="datatable"] tbody tr') == 2
    assert page.get_text('[data-test="datatable"] tbody tr:first-child td:nth-child(1)') == "2023-01-02"
    assert page.get_text('[data-test="datatable"] tbody tr:nth-child(2) td:nth-child(1)') == "2023-01-03"


def test_applies_datetime_range_filter(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = "dummy"
        datasource = InMemoryDataSource(
            Post,
            [
                Post(updated_at=datetime.datetime(2023, 1, 1, 12, 0, 0)),
                Post(updated_at=datetime.datetime(2023, 1, 2, 12, 0, 0)),
                Post(updated_at=datetime.datetime(2023, 1, 3, 12, 0, 0)),
                Post(updated_at=datetime.datetime(2023, 1, 4, 12, 0, 0)),
            ],
        )
        columns = [TableColumn(name="updated_at")]
        filters = [filters.DateTimeRangeFilter("updated_at")]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get("/admin/dummy?updated_at-after=2023-01-01 10:00:00&updated_at-before=2023-01-01 14:00:00")
    page = MarkupSelector(response.text)
    assert page.count('[data-test="datatable"] tbody tr') == 1
    assert page.get_text('[data-test="datatable"] tbody tr:first-child td:nth-child(1)') == "2023-01-01 12:00:00"


def test_applies_choice_filter(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = "dummy"
        datasource = InMemoryDataSource(Post, [Post(title="Title 1"), Post(title="Title 2")])
        columns = [TableColumn(name="title")]
        filters = [filters.ChoiceFilter("title", choices=["Title 1"])]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get("/admin/dummy?title-choice=Title 1")
    page = MarkupSelector(response.text)
    assert page.count('[data-test="datatable"] tbody tr') == 1
    assert page.get_text('[data-test="datatable"] tbody tr:first-child td:nth-child(1)') == "Title 1"


def test_applies_multichoice_filter(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = "dummy"
        datasource = InMemoryDataSource(Post, [Post(title="Title 1"), Post(title="Title 2"), Post(title="Title 3")])
        columns = [TableColumn(name="title")]
        filters = [filters.MultiChoiceFilter("title", choices=["Title 1", "Title 2"])]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get("/admin/dummy?title-choice=Title 1&title-choice=Title 2")
    page = MarkupSelector(response.text)
    assert page.count('[data-test="datatable"] tbody tr') == 2
    assert page.get_text('[data-test="datatable"] tbody tr:first-child td:nth-child(1)') == "Title 1"
    assert page.get_text('[data-test="datatable"] tbody tr:nth-child(2) td:nth-child(1)') == "Title 2"


def test_request_content_rendering(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = "dummy"
        datasource = InMemoryDataSource(Post, [Post(title="Title 1"), Post(title="Title 2"), Post(title="Title 3")])
        columns = [TableColumn(name="title")]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get("/admin/dummy", headers={"hx-target": "data"})
    assert response.headers["hx-push-url"] == "http://testserver/admin/dummy/"
    assert response.headers["hx-trigger-after-settle"] == '{"filters-reload": ""}'
    page = MarkupSelector(response.text)
    assert page.has_node('[data-test="datatable"]')


def test_request_filterbar_rendering(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = "dummy"
        datasource = InMemoryDataSource(Post, [Post(title="Title 1"), Post(title="Title 2"), Post(title="Title 3")])
        columns = [TableColumn(name="title")]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get("/admin/dummy", headers={"hx-target": "filter-bar"})
    page = MarkupSelector(response.text)
    assert page.has_node('[data-test="filters-bar"]')


def test_clears_filter_bar(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = "dummy"
        datasource = InMemoryDataSource(Post, [Post(title="Title 1"), Post(title="Title 2"), Post(title="Title 3")])
        columns = [TableColumn(name="title")]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get("/admin/dummy?clear", headers={"hx-target": "filter-bar"})
    assert response.headers["hx-push-url"] == "http://testserver/admin/dummy/"
    assert response.headers["hx-trigger-after-settle"] == '{"refresh-datatable": ""}'
    page = MarkupSelector(response.text)
    assert page.has_node('[data-test="filters-bar"]')
