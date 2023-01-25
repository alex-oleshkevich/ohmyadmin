import pytest
import typing
import wtforms
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from ohmyadmin import actions
from ohmyadmin.datasource.memory import InMemoryDataSource
from ohmyadmin.pages.table import TablePage
from ohmyadmin.testing import MarkupSelector
from ohmyadmin.views.table import TableColumn
from tests.conftest import CreateTestAppFactory
from tests.models import Post

datasource = InMemoryDataSource(Post, [Post(title='Title 1'), Post(title='Title 2'), Post(title='Title 3')])


class ExamplePageAction(actions.BasePageAction):
    slug = 'example'
    label = 'Example Action'

    async def apply(self, request: Request) -> Response:
        return Response(f'ACTION {request.method}')


class ExampleForm(wtforms.Form):
    name = wtforms.StringField()


class ExampleFormAction(actions.BaseFormPageAction):
    slug = 'form'
    label = 'Form Action'
    form_class = ExampleForm

    async def handle(self, request: Request, form: wtforms.Form, model: typing.Any) -> Response:
        return Response('FORM SUBMIT')


def test_renders_link_page_actions(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        page_actions = [actions.Link(label='Link Action', url='/')]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert page.get_node_text('[data-test="page-actions"]') == 'Link Action'


def test_renders_dispatchable_page_actions(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        page_actions = [ExamplePageAction()]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert page.get_node_text('[data-test="page-actions"]') == 'Example Action'


@pytest.mark.parametrize('http_method', ['get', 'post', 'put', 'patch', 'delete'])
def test_dispatches_page_actions(create_test_app: CreateTestAppFactory, http_method: str) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        page_actions = [ExamplePageAction()]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    callback = getattr(client, http_method)
    response = callback('/admin/dummy?_action=example')
    assert response.text == f'ACTION {http_method.upper()}'


def test_dispatches_form_actions(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        page_actions = [ExampleFormAction()]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get('/admin/dummy?_action=form')
    page = MarkupSelector(response.text)
    assert page.has_node('form')

    response = client.post('/admin/dummy?_action=form', data={'name': 'test'})
    assert response.status_code == 200
    assert response.text == 'FORM SUBMIT'


def test_undefined_action(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]

    with pytest.raises(actions.UndefinedActionError, match='Action "undefined" is not defined.'):
        client = TestClient(create_test_app(pages=[DummyTable()]))
        client.get('/admin/dummy?_action=undefined')
