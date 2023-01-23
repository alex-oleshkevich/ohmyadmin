import json
import pytest
import typing
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount
from starlette.testclient import TestClient

from examples.models import User
from ohmyadmin import actions
from ohmyadmin.actions import ActionResponse
from ohmyadmin.app import OhMyAdmin
from ohmyadmin.datasource.memory import InMemoryDataSource
from ohmyadmin.pages.table import TablePage
from tests.utils import AuthTestPolicy


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
    datasource = InMemoryDataSource([User(id='1')])
    object_actions = [
        actions.ObjectLink('Link action', url='http://example.com'),
        actions.ObjectCallback('refresh', 'Refresh page', example_callback_action),
        actions.ObjectCallback('form', label='Form modal', callback=_FormModal()),
    ]


app = Starlette(
    routes=[Mount('/admin', OhMyAdmin(pages=[_DemoPageActions()], auth_policy=AuthTestPolicy()))],
    middleware=[Middleware(SessionMiddleware, secret_key='key!')],
)


def test_renders_link_action() -> None:
    client = TestClient(app)
    response = client.get('/admin/demo')
    assert response.status_code == 200
    assert 'Link action' in response.text
    assert 'href="http://example.com"' in response.text


def test_renders_callback_action() -> None:
    client = TestClient(app)
    response = client.get('/admin/demo')
    assert response.status_code == 200
    assert 'Refresh page' in response.text
    assert '_action=refresh' in response.text


@pytest.mark.parametrize('http_method', ['get', 'post'])
def test_dispatches_callback_action(http_method: typing.Literal['get', 'post']) -> None:
    client = TestClient(app)
    callback = getattr(client, http_method)
    response = callback('/admin/demo?_object_action=refresh')
    assert response.status_code == 204
    assert 'hx-refresh' in response.headers


def test_dispatches_modal_action() -> None:
    client = TestClient(app)
    response = client.get('/admin/demo?_object_action=form')
    assert response.status_code == 200
    assert 'Modal title' in response.text

    response = client.post('/admin/demo?_object_action=form', data={'first_name': 'root', 'last_name': 'localhost'})
    assert json.loads(response.headers['hx-trigger']) == {'toast': {'message': 'submit', 'category': 'success'}}


def test_raises_for_unknown_action() -> None:
    with pytest.raises(ValueError, match='Object action "unknown" is not defined.'):
        client = TestClient(app)
        client.get('/admin/demo?_object_action=unknown')
