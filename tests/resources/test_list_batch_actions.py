from starlette.testclient import TestClient

from ohmyadmin.testing import MarkupSelector


def test_renders_batch_actions_dropdown(client: TestClient) -> None:
    response = client.get('/admin/resources/demo')
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.get_text('[data-test="batch-action-selector"] option:nth-child(2)') == 'Toast'


def test_renders_default_batch_actions_dropdown(client: TestClient) -> None:
    response = client.get('/admin/resources/demo')
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.get_text('[data-test="batch-action-selector"] option:nth-child(3)') == 'Mass delete'


def test_renders_row_selection_checkbox(client: TestClient) -> None:
    response = client.get('/admin/resources/demo')
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.count('[data-test="datatable"] x-batch-toggle') == 25


def test_dispatches_page_action(client: TestClient) -> None:
    response = client.post('/admin/resources/demo?_batch_action=example')
    assert response.text == 'ok'
