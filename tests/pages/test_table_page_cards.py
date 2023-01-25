from starlette.requests import Request
from starlette.testclient import TestClient

from ohmyadmin.datasource.memory import InMemoryDataSource
from ohmyadmin.metrics import ValueMetric
from ohmyadmin.pages.table import TablePage
from ohmyadmin.views.table import TableColumn
from tests.conftest import CreateTestAppFactory
from tests.models import Post


class ExampleCard(ValueMetric):
    slug = 'example'

    async def calculate(self, request: Request) -> str:
        return 'CARD DATA'


def test_renders_cards(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = InMemoryDataSource(Post, [Post(title='Title 1'), Post(title='Title 2'), Post(title='Title 3')])
        columns = [TableColumn(name='title')]
        metrics = [ExampleCard]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get('/admin/dummy')
    assert '_metric=example' in response.text


def test_dispatches_cards(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = InMemoryDataSource(Post, [Post(title='Title 1'), Post(title='Title 2'), Post(title='Title 3')])
        columns = [TableColumn(name='title')]
        metrics = [ExampleCard]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get('/admin/dummy?_metric=example')
    assert 'CARD DATA' in response.text
