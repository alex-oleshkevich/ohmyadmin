from starlette.testclient import TestClient

from ohmyadmin.testing import MarkupSelector


def test_renders_object_actions(client: TestClient) -> None:
    response = client.get('/admin/resources/demo')
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.get_text('[data-test="datatable"] tbody tr:first-child .list-menu-item:first-child') == 'Toast'


def test_renders_default_object_actions(client: TestClient) -> None:
    response = client.get('/admin/resources/demo')
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.get_text('[data-test="datatable"] tbody tr:first-child .list-menu-item:nth-child(2)') == 'Edit'
    assert (
        selector.get_attribute(
            '[data-test="datatable"] tbody tr:first-child .list-menu-item:nth-child(2)',
            'href',
        )
        == 'http://testserver/admin/resources/demo/1/edit'
    )
    assert selector.get_text('[data-test="datatable"] tbody tr:first-child .list-menu-item:nth-child(3)') == 'Delete'
    assert (
        selector.get_attribute(
            '[data-test="datatable"] tbody tr:first-child .list-menu-item:nth-child(3)',
            'hx-delete',
        )
        == 'http://testserver/admin/resources/demo/?_object_action=delete&_ids=1'
    )
    assert (
        selector.get_attribute(
            '[data-test="datatable"] tbody tr:first-child .list-menu-item:nth-child(3)',
            'hx-confirm',
        )
        == 'Are you sure you want to delete this record?'
    )


def test_dispatches_page_action(client: TestClient) -> None:
    response = client.get('/admin/resources/demo/?_object_action=example&_ids=1')
    assert response.text == 'ok'
