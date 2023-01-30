from starlette.testclient import TestClient

from ohmyadmin.testing import MarkupSelector


def test_renders_page_actions(client: TestClient) -> None:
    response = client.get('/admin/resources/demo')
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.get_text('[data-test="page-actions"] a:first-child') == 'Link Action'
    assert selector.get_text('[data-test="page-actions"] button') == 'Toast'


def test_dispatches_page_action(client: TestClient) -> None:
    response = client.get('/admin/resources/demo?_action=example')
    assert response.text == 'ok'
