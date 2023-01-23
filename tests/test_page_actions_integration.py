import json
import pytest
import typing
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from ohmyadmin import actions
from ohmyadmin.actions import ActionResponse
from ohmyadmin.datasource.memory import InMemoryDataSource
from ohmyadmin.pages.table import TablePage
from tests.utils import create_test_app


async def example_callback_action(request: Request) -> ActionResponse:
    return ActionResponse().refresh()


class _FormModal(actions.Modal):
    title = 'Modal title'

    async def dispatch(self, request: Request) -> Response:
        if request.method == 'POST':
            return ActionResponse().show_toast('submit')
        return self.render(request)


class _DemoPageActions(TablePage):
    slug = 'demo'
    datasource = InMemoryDataSource([])
    page_actions = [
        actions.Link('Link action', url='http://example.com'),
        actions.Callback('refresh', 'Refresh page', example_callback_action),
        actions.Callback('form', label='Form modal', callback=_FormModal()),
    ]


app = create_test_app([_DemoPageActions()])


def test_renders_link_page_action() -> None:
    client = TestClient(app)
    response = client.get('/admin/demo')
    assert response.status_code == 200
    assert 'Link action' in response.text
    assert 'href="http://example.com"' in response.text


def test_renders_callback_page_action() -> None:
    client = TestClient(app)
    response = client.get('/admin/demo')
    assert response.status_code == 200
    assert 'Refresh page' in response.text
    assert '_action=refresh' in response.text


@pytest.mark.parametrize('http_method', ['get', 'post'])
def test_dispatches_callback_action(http_method: typing.Literal['get', 'post']) -> None:
    client = TestClient(app)
    callback = getattr(client, http_method)
    response = callback('/admin/demo?_action=refresh')
    assert response.status_code == 204
    assert 'hx-refresh' in response.headers


def test_dispatches_modal_action() -> None:
    client = TestClient(app)
    response = client.get('/admin/demo?_action=form')
    assert response.status_code == 200
    assert 'Modal title' in response.text

    response = client.post('/admin/demo?_action=form', data={'first_name': 'root', 'last_name': 'localhost'})
    assert json.loads(response.headers['hx-trigger']) == {'toast': {'message': 'submit', 'category': 'success'}}


def test_raises_for_unknown_action() -> None:
    with pytest.raises(ValueError, match='Action "unknown" is not defined.'):
        client = TestClient(app)
        client.get('/admin/demo?_action=unknown')
