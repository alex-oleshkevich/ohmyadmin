import pytest
import wtforms
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from ohmyadmin import actions
from ohmyadmin.datasources.datasource import InMemoryDataSource
from ohmyadmin.pages.table import TablePage
from ohmyadmin.testing import MarkupSelector
from ohmyadmin.views.table import TableColumn
from tests.conftest import CreateTestAppFactory
from tests.models import Post

datasource = InMemoryDataSource(Post, [Post(title='Title 1'), Post(title='Title 2'), Post(title='Title 3')])


class ExampleForm(wtforms.Form):
    name = wtforms.StringField()


class ExampleAction(actions.BaseBatchAction):
    slug = 'example'
    label = 'Example Action'
    form_class = ExampleForm

    async def apply(self, request: Request, object_ids: list[str], form: wtforms.Form) -> Response:
        return Response(f'ACTION {request.method} object_ids={object_ids}')


def test_renders_batch_action_selector(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        batch_actions = [ExampleAction()]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert page.get_text('[data-test="batch-action-selector"] option:nth-child(2)') == 'Example Action'


def test_renders_row_selection_checkboxes(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        batch_actions = [ExampleAction()]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert page.has_node('[data-test="datatable"] tr td:first-child x-batch-toggle')


def test_shows_confirmation_modal_on_action_run(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        batch_actions = [ExampleAction()]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get('/admin/dummy?_batch_action=example&_ids=1&_ids=2')
    page = MarkupSelector(response.text)
    assert page.get_text('form.modal-dialog header') == 'Example Action'


def test_calls_batch_action(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        batch_actions = [ExampleAction()]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.post('/admin/dummy?_batch_action=example&_ids=1&_ids=2')
    assert response.text == "ACTION POST object_ids=['1', '2']"


def test_undefined_action(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]

    with pytest.raises(actions.UndefinedActionError, match='Batch action "undefined" is not defined.'):
        client = TestClient(create_test_app(pages=[DummyTable()]))
        client.get('/admin/dummy?_batch_action=undefined')
