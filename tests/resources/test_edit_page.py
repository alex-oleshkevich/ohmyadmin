from starlette.testclient import TestClient

from ohmyadmin import actions
from ohmyadmin.testing import MarkupSelector
from tests.conftest import CreateTestAppFactory
from tests.resources.demo_resource import DemoResource


def test_renders_edit_form(client: TestClient) -> None:
    response = client.get('/admin/resources/demo/90/edit')
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.has_node('form input[type="text"][name="title"]')
    assert selector.get_attribute('form input[type="text"][name="title"]', 'value') == 'Title 90'


def test_validates_form(client: TestClient) -> None:
    response = client.post('/admin/resources/demo/90/edit', data={'title': ''})
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.get_text('form .form-errors') == 'This field is required.'


def test_submits_form_and_continue_edit(client: TestClient) -> None:
    response = client.post('/admin/resources/demo/90/edit', data={'title': 'new title', '_continue': ''})
    assert response.status_code == 204
    assert 'hx-redirect' not in response.headers
    assert 'has been updated' in response.headers['hx-trigger']


def test_submits_form_and_returns(client: TestClient) -> None:
    response = client.post('/admin/resources/demo/90/edit', data={'title': 'new title', '_return': ''})
    assert response.status_code == 204
    assert response.headers['hx-redirect'] == 'http://testserver/admin/resources/demo/'


def test_renders_form_actions(client: TestClient) -> None:
    response = client.get('/admin/resources/demo/90/edit')
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.get_text('form .form-actions button[type="submit"].btn-accent') == 'Update and return to list'
    assert selector.get_text('form .form-actions button[type="submit"]:nth-child(2)') == 'Update and continue editing'
    assert selector.get_text('form .form-actions a.btn-link') == 'Return to list'


def test_renders_custom_form_actions(create_test_app: CreateTestAppFactory) -> None:
    class MyResource(DemoResource):
        slug = 'demo'
        update_form_actions = [actions.Submit(label='Update')]

    app = create_test_app(pages=[MyResource()])
    client = TestClient(app)
    response = client.get('/admin/resources/demo/90/edit')
    selector = MarkupSelector(response.text)
    assert response.status_code == 200
    assert selector.count('form .form-actions button') == 1
    assert selector.get_text('form .form-actions button[type="submit"]:first-child') == 'Update'
