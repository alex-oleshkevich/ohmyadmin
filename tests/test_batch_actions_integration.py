import json
import pytest
import wtforms
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from examples.models import User
from ohmyadmin.actions import ActionResponse, BaseBatchAction
from ohmyadmin.datasource.memory import InMemoryDataSource
from ohmyadmin.pages.table import TablePage
from tests.utils import create_test_app


class _ExampleBatchAction(BaseBatchAction):
    label = 'Example batch action'

    async def apply(self, request: Request, object_ids: list[str], form: wtforms.Form) -> Response:
        return ActionResponse().show_toast('submit')


class _DemoPageActions(TablePage):
    slug = 'demo'
    datasource = InMemoryDataSource([User(id='1')])
    batch_actions = [_ExampleBatchAction(slug='example')]


app = create_test_app([_DemoPageActions()])


def test_renders_action() -> None:
    client = TestClient(app)
    response = client.get('/admin/demo')
    assert response.status_code == 200
    assert 'Example batch action' in response.text


def test_renders_modal() -> None:
    client = TestClient(app)
    response = client.get('/admin/demo?_batch_action=example')
    assert response.status_code == 200
    assert 'x-modal' in response.text
    assert 'Example batch action' in response.text


def test_executes_action() -> None:
    client = TestClient(app)
    response = client.post('/admin/demo?_batch_action=example&_ids=1')
    assert response.status_code == 204
    assert json.loads(response.headers['hx-trigger']) == {'toast': {'message': 'submit', 'category': 'success'}}


def test_raises_for_unknown_action() -> None:
    with pytest.raises(ValueError, match='Batch action "unknown" is not defined.'):
        client = TestClient(app)
        client.get('/admin/demo?_batch_action=unknown')
