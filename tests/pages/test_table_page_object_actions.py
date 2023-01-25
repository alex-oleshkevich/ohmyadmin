import pytest
import typing
import wtforms
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from ohmyadmin import actions
from ohmyadmin.actions import BaseObjectAction
from ohmyadmin.datasource.memory import InMemoryDataSource
from ohmyadmin.pages.table import TablePage
from ohmyadmin.testing import MarkupSelector
from ohmyadmin.views.table import TableColumn
from tests.conftest import CreateTestAppFactory
from tests.models import Post

datasource = InMemoryDataSource(Post, [Post(title='Title 1'), Post(title='Title 2'), Post(title='Title 3')])


class ExampleObjectAction(BaseObjectAction):
    slug = 'example'
    label = 'Example Object Action'

    async def apply(self, request: Request, object_id: str) -> Response:
        return Response(f'OBJECT ACTION {request.method} id={object_id}')


class ExampleForm(wtforms.Form):
    name = wtforms.StringField()


class ExampleFormAction(actions.BaseFormObjectAction):
    slug = 'form'
    label = 'Form Action'
    form_class = ExampleForm

    async def handle(self, request: Request, form: wtforms.Form, model: typing.Any) -> Response:
        return Response('FORM SUBMIT')


def test_renders_link_object_actions(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        object_actions = [actions.ObjectLink(label='Link Action', url='/')]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert page.get_node_text('td[data-test="table-object-actions"]') == 'Link Action'


def test_renders_object_actions(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        object_actions = [ExampleObjectAction()]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get('/admin/dummy')
    page = MarkupSelector(response.text)
    assert page.get_node_text('td[data-test="table-object-actions"]') == 'Example Object Action'


@pytest.mark.parametrize('http_method', ['get', 'post', 'put', 'patch', 'delete'])
def test_dispatches_object_action(create_test_app: CreateTestAppFactory, http_method: str) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        object_actions = [ExampleObjectAction()]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    callback = getattr(client, http_method)
    response = callback('/admin/dummy?_object_action=example&_ids=1')
    assert response.text == f'OBJECT ACTION {http_method.upper()} id=1'


def test_returns_toast_if_no_object_passed(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        object_actions = [ExampleObjectAction()]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get('/admin/dummy?_object_action=example')
    assert response.status_code == 204
    assert 'No object selected.' in response.headers['hx-trigger']


def test_dispatches_form_action(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]
        object_actions = [ExampleFormAction()]

    client = TestClient(create_test_app(pages=[DummyTable()]))
    response = client.get('/admin/dummy?_object_action=form&_ids=1')
    page = MarkupSelector(response.text)
    assert page.has_node('form')

    response = client.post('/admin/dummy?_object_action=form&_ids=1')
    assert 'FORM SUBMIT' in response.text


def test_undefined_action(create_test_app: CreateTestAppFactory) -> None:
    class DummyTable(TablePage):
        slug = 'dummy'
        datasource = datasource
        columns = [TableColumn(name='title')]

    with pytest.raises(actions.UndefinedActionError, match='Object action "undefined" is not defined.'):
        client = TestClient(create_test_app(pages=[DummyTable()]))
        client.get('/admin/dummy?_object_action=undefined')
