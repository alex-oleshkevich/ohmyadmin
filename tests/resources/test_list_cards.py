from starlette.testclient import TestClient

from ohmyadmin.testing import MarkupSelector


def test_renders_cards(client: TestClient) -> None:
    response = client.get('/admin/resources/demo')
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.count('[data-test="cards"]') == 1


def test_dispatches_card(client: TestClient) -> None:
    response = client.get('/admin/resources/demo?_metric=example')
    assert 'CALLED' in response.text
