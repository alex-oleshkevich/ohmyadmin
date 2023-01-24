import dataclasses

from starlette.testclient import TestClient

from ohmyadmin.datasource.memory import InMemoryDataSource
from ohmyadmin.filters import StringFilter
from ohmyadmin.pages.table import TablePage
from ohmyadmin.testing import MarkupSelector
from ohmyadmin.views.table import TableColumn
from tests.conftest import CreateTestAppFactory


@dataclasses.dataclass
class Post:
    id: str
    title: str
    published: bool


class DummyTablePage(TablePage):
    slug = 'dummy'
    page_size = 5
    datasource = InMemoryDataSource([Post(id=str(index), title=f'Post {index}', published=True) for index in range(20)])
    columns = [
        TableColumn(name='id'),
        TableColumn(name='title'),
        TableColumn(name='published'),
    ]


class DummyTablePageWithSortableColumns(TablePage):
    slug = 'dummy'
    datasource = InMemoryDataSource([Post(id=str(index), title=f'Post {index}', published=True) for index in range(20)])
    columns = [
        TableColumn(name='id', sortable=True),
        TableColumn(name='title', searchable=True),
        TableColumn(name='published'),
    ]


class DummyTablePageWithSearchableColumns(TablePage):
    slug = 'dummy'
    datasource = InMemoryDataSource([Post(id=str(index), title=f'Post {index}', published=True) for index in range(20)])
    columns = [
        TableColumn(name='id'),
        TableColumn(name='title', searchable=True),
        TableColumn(name='published'),
    ]


class DummyTablePageWithFilters(TablePage):
    slug = 'dummy'
    datasource = InMemoryDataSource([Post(id=str(index), title=f'Post {index}', published=True) for index in range(20)])
    columns = [
        TableColumn(name='id'),
        TableColumn(name='title'),
        TableColumn(name='published'),
    ]
    filters = [
        StringFilter('title'),
    ]


def test_page_accessible(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get('/admin/dummy')
    assert response.status_code == 200


def test_renders_columns(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert page.get_node_text('table thead tr th:nth-child(1)') == 'Id'
    assert page.get_node_text('table thead tr th:nth-child(2)') == 'Title'
    assert page.get_node_text('table thead tr th:nth-child(3)') == 'Published'


def test_renders_sortable_columns(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePageWithSortableColumns()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert 'ordering' in page.find_node('table thead tr th:first-child a')['href']


def test_not_renders_sortable_columns(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert not page.has_node('table thead tr th:first-child a')


def test_renders_search_input(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePageWithSearchableColumns()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert page.has_node('input[type="search"][name="search"]')


def test_not_renders_search_input(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert not page.has_node('input[type="search"][name="search"]')


def test_renders_pagination(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert page.has_node('[data-test="pagination"]')


def test_renders_pagination_buttons(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert page.get_node_text('[data-test="pagination-control"]:first-child') == '1'


def test_renders_filters(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePageWithFilters()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert page.has_node('[data-test="filters-trigger"]')
    assert page.has_node('[data-test="filters-bar"]')
    assert page.count('[data-test="filter"]') == 1


def test_not_renders_filters(create_test_app: CreateTestAppFactory) -> None:
    client = TestClient(create_test_app(pages=[DummyTablePage()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert not page.has_node('[data-test="filters-trigger"]')
